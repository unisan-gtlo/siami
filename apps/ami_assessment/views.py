from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import ButirPenilaian, Siklus, Standar

from .forms import DokumenBuktiForm, DokumenVerifikasiForm, JawabanButirForm
from .models import DokumenBukti, JawabanButir, Pengisian


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


@login_required
def pengisian_detail(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(
            request,
            'Akun Anda belum terhubung ke profil AMI (prodi). Hubungi LP3M/admin '
            'untuk melengkapi data UserAmi Anda.',
        )
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'self_assessment'})

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None:
        messages.error(request, 'Belum ada siklus AMI yang aktif saat ini.')
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'self_assessment'})

    pengisian, _ = Pengisian.objects.get_or_create(
        siklus=siklus, prodi=user_ami.prodi,
        defaults={'status': 'sedang_diisi', 'started_at': timezone.now(), 'operator': user_ami},
    )

    butir_qs = ButirPenilaian.objects.filter(siklus=siklus, is_aktif=True).select_related('standar')
    jawaban_by_butir = {
        j.butir_id: j for j in JawabanButir.objects.filter(pengisian=pengisian)
    }

    all_rows = []
    for butir in butir_qs.order_by('standar__no_urut', 'no_urut'):
        all_rows.append({
            'butir': butir,
            'jawaban': jawaban_by_butir.get(butir.id),
        })

    total = len(all_rows)
    terisi = sum(1 for r in all_rows if r['jawaban'] and r['jawaban'].is_terisi)
    if pengisian.total_butir != total or pengisian.butir_terisi != terisi:
        pengisian.total_butir = total
        pengisian.butir_terisi = terisi
        pengisian.save(update_fields=['total_butir', 'butir_terisi', 'updated_at'])

    # Navigasi 9 standar dengan progress per standar, mirip mockup.
    standar_nav = []
    for standar in Standar.objects.filter(is_aktif=True).order_by('no_urut'):
        rows_standar = [r for r in all_rows if r['butir'].standar_id == standar.id]
        standar_nav.append({
            'standar': standar,
            'total': len(rows_standar),
            'terisi': sum(1 for r in rows_standar if r['jawaban'] and r['jawaban'].is_terisi),
        })

    standar_id = request.GET.get('standar')
    if standar_id:
        rows = [r for r in all_rows if str(r['butir'].standar_id) == standar_id]
    else:
        rows = all_rows

    return render(request, 'ami_assessment/pengisian_detail.html', {
        'pengisian': pengisian,
        'rows': rows,
        'standar_nav': standar_nav,
        'standar_id': standar_id,
        'active_tab': 'self_assessment',
    })


@login_required
def jawaban_edit(request, butir_id):
    user_ami = _get_user_ami(request)
    if user_ami is None or user_ami.prodi_id is None:
        return redirect('self_assessment:pengisian_detail')

    siklus = Siklus.objects.filter(is_current=True).first()
    butir = get_object_or_404(ButirPenilaian, pk=butir_id, siklus=siklus)
    pengisian = get_object_or_404(Pengisian, siklus=siklus, prodi=user_ami.prodi)

    jawaban, _ = JawabanButir.objects.get_or_create(pengisian=pengisian, butir=butir)

    if jawaban.is_locked:
        messages.error(request, 'Jawaban ini sudah dikunci dan tidak bisa diedit lagi.')
        return redirect('self_assessment:pengisian_detail')

    if request.method == 'POST':
        form = JawabanButirForm(request.POST, instance=jawaban, jenis_input=butir.jenis_input)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.is_terisi = bool(
                obj.nilai_kuantitatif is not None or obj.nilai_pilihan or obj.nilai_narasi
            )
            obj.diisi_oleh = user_ami
            obj.diisi_pada = timezone.now()
            obj.save()
            messages.success(request, f'Jawaban butir {butir.kode} tersimpan.')
            return redirect('self_assessment:pengisian_detail')
    else:
        form = JawabanButirForm(instance=jawaban, jenis_input=butir.jenis_input)

    butir_standar = list(
        ButirPenilaian.objects.filter(siklus=siklus, standar=butir.standar, is_aktif=True).order_by('no_urut'),
    )
    idx = next((i for i, b in enumerate(butir_standar) if b.id == butir.id), None)
    butir_sebelumnya = butir_standar[idx - 1] if idx is not None and idx > 0 else None
    butir_selanjutnya = butir_standar[idx + 1] if idx is not None and idx < len(butir_standar) - 1 else None

    return render(request, 'ami_assessment/jawaban_form.html', {
        'form': form, 'butir': butir, 'pengisian': pengisian,
        'butir_sebelumnya': butir_sebelumnya, 'butir_selanjutnya': butir_selanjutnya,
        'active_tab': 'self_assessment',
    })


@login_required
def upload_bukti(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'upload'})

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None:
        messages.error(request, 'Belum ada siklus AMI yang aktif saat ini.')
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'upload'})

    # get_or_create supaya konsisten dengan pengisian_detail/jawaban_edit --
    # sebelumnya pakai filter().first(), jadi upload gagal diam-diam kalau
    # auditee belum pernah membuka tab Self-Assessment dulu.
    pengisian, _ = Pengisian.objects.get_or_create(
        siklus=siklus, prodi=user_ami.prodi,
        defaults={'status': 'sedang_diisi', 'started_at': timezone.now(), 'operator': user_ami},
    )

    if request.method == 'POST':
        form = DokumenBuktiForm(request.POST, request.FILES, siklus=siklus)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.pengisian = pengisian
            obj.diunggah_oleh = user_ami
            obj.save()
            messages.success(request, f'Dokumen "{obj.nama_dokumen}" berhasil ditambahkan.')
            return redirect('self_assessment:upload_bukti')
    else:
        form = DokumenBuktiForm(siklus=siklus)

    dokumen_list = DokumenBukti.objects.filter(pengisian=pengisian).select_related('butir')

    stats = {
        'total': len(dokumen_list),
        'terverifikasi': sum(1 for d in dokumen_list if d.status == 'terverifikasi'),
        'menunggu': sum(1 for d in dokumen_list if d.status in ('belum_diverifikasi', 'menunggu_upm')),
        'revisi': sum(1 for d in dokumen_list if d.status in ('ditolak', 'perlu_revisi')),
    }

    return render(request, 'ami_assessment/upload_bukti.html', {
        'form': form, 'dokumen_list': dokumen_list, 'stats': stats,
        'active_tab': 'upload',
    })


def _can_verify(request):
    user_ami = _get_user_ami(request)
    return request.user.is_superuser or (user_ami and (
        user_ami.is_lp3m or user_ami.is_upm or user_ami.is_auditor_de
    ))


@login_required
def dokumen_verifikasi_list(request):
    if not _can_verify(request):
        messages.error(request, 'Halaman ini hanya untuk UPM/Auditor DE/LP3M.')
        return render(request, 'ami_assessment/forbidden.html', {'active_tab': 'verifikasi'})

    user_ami = _get_user_ami(request)
    siklus = Siklus.objects.filter(is_current=True).first()

    dokumen_qs = DokumenBukti.objects.filter(pengisian__siklus=siklus).select_related(
        'pengisian__prodi__fakultas', 'butir',
    ).order_by('status', '-diunggah_pada')

    # UPM (bukan LP3M/superuser) hanya lihat dokumen dari prodi di fakultasnya sendiri --
    # mencegah UPM memvalidasi lintas fakultas yang bukan wewenangnya.
    is_pengawas_penuh = request.user.is_superuser or (user_ami and user_ami.is_lp3m)
    if not is_pengawas_penuh and user_ami and user_ami.is_upm and user_ami.fakultas_id:
        dokumen_qs = dokumen_qs.filter(pengisian__prodi__fakultas_id=user_ami.fakultas_id)

    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'pending':
        dokumen_qs = dokumen_qs.filter(status__in=['belum_diverifikasi', 'menunggu_upm'])
    elif status_filter != 'semua':
        dokumen_qs = dokumen_qs.filter(status=status_filter)

    return render(request, 'ami_assessment/dokumen_verifikasi_list.html', {
        'dokumen_list': dokumen_qs, 'status_filter': status_filter,
        'active_tab': 'verifikasi',
    })


@login_required
def dokumen_verifikasi_action(request, dokumen_id):
    if not _can_verify(request):
        messages.error(request, 'Halaman ini hanya untuk UPM/Auditor DE/LP3M.')
        return redirect('self_assessment:dokumen_verifikasi_list')

    user_ami = _get_user_ami(request)
    dokumen = get_object_or_404(DokumenBukti, pk=dokumen_id)

    if request.method == 'POST':
        form = DokumenVerifikasiForm(request.POST, instance=dokumen)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.diverifikasi_oleh = user_ami
            obj.diverifikasi_pada = timezone.now()
            obj.save()
            messages.success(request, f'Status dokumen "{obj.nama_dokumen}" berhasil diperbarui.')
            return redirect('self_assessment:dokumen_verifikasi_list')
    else:
        form = DokumenVerifikasiForm(instance=dokumen)

    return render(request, 'ami_assessment/dokumen_verifikasi_form.html', {
        'form': form, 'dokumen': dokumen, 'active_tab': 'verifikasi',
    })
