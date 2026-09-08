from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import ButirPenilaian, MasterStandar, Siklus, butir_untuk_cakupan

from .forms import DokumenBuktiForm, DokumenVerifikasiForm, JawabanButirForm
from .models import DokumenBukti, JawabanButir, Pengisian


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


def _get_pengisian_untuk_user(user_ami, siklus):
    """Tentukan cakupan Pengisian milik user (prodi > fakultas-UPM >
    universitas-LP3M/Pimpinan, urutan prioritas) dan get_or_create baris
    yang sesuai. Return None kalau user tidak punya akses ke cakupan
    manapun -- lihat plan sasaran_auditee non-Prodi."""
    if user_ami is None:
        return None
    if user_ami.prodi_id:
        pengisian, _ = Pengisian.objects.get_or_create(
            siklus=siklus, cakupan='prodi', prodi=user_ami.prodi,
            defaults={'status': 'sedang_diisi', 'started_at': timezone.now(), 'operator': user_ami},
        )
        return pengisian
    if user_ami.is_upm and user_ami.fakultas_id:
        pengisian, _ = Pengisian.objects.get_or_create(
            siklus=siklus, cakupan='fakultas', fakultas=user_ami.fakultas,
            defaults={'status': 'sedang_diisi', 'started_at': timezone.now(), 'operator': user_ami},
        )
        return pengisian
    if user_ami.is_lp3m or user_ami.is_pimpinan:
        pengisian, _ = Pengisian.objects.get_or_create(
            siklus=siklus, cakupan='universitas',
            defaults={'status': 'sedang_diisi', 'started_at': timezone.now(), 'operator': user_ami},
        )
        return pengisian
    return None


@login_required
def pengisian_detail(request):
    user_ami = _get_user_ami(request)
    siklus = Siklus.objects.filter(is_current=True).first()
    pengisian = _get_pengisian_untuk_user(user_ami, siklus) if siklus else None

    if pengisian is None:
        messages.error(
            request,
            'Akun Anda belum terhubung ke profil AMI (prodi/fakultas) atau belum ada '
            'siklus AMI aktif. Hubungi LP3M/admin untuk melengkapi data UserAmi Anda.',
        )
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'self_assessment'})

    butir_qs = butir_untuk_cakupan(
        ButirPenilaian.objects.filter(siklus=siklus, is_aktif=True), pengisian.cakupan,
    ).select_related('standar', 'master_standar')
    jawaban_by_butir = {
        j.butir_id: j for j in JawabanButir.objects.filter(pengisian=pengisian)
    }

    all_rows = []
    for butir in butir_qs.order_by('master_standar__no_urut', 'standar__no_urut', 'no_urut'):
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

    # Navigasi per Master Standar (Pasal 5 SN-Dikti, Permendiktisaintek
    # 39/2025) -- menggantikan navigasi 9 Standar lama, yang taksonominya
    # institusional UNISAN sendiri dan tidak dipetakan ke 98 butir baru
    # (semuanya numpuk di satu slot placeholder "9. Luaran").
    standar_nav = []
    for master_standar in MasterStandar.objects.order_by('no_urut'):
        rows_standar = [r for r in all_rows if r['butir'].master_standar_id == master_standar.id]
        if not rows_standar:
            continue
        standar_nav.append({
            'master_standar': master_standar,
            'total': len(rows_standar),
            'terisi': sum(1 for r in rows_standar if r['jawaban'] and r['jawaban'].is_terisi),
        })
    tanpa_master_standar = [r for r in all_rows if r['butir'].master_standar_id is None]
    if tanpa_master_standar:
        standar_nav.append({
            'master_standar': None,
            'total': len(tanpa_master_standar),
            'terisi': sum(1 for r in tanpa_master_standar if r['jawaban'] and r['jawaban'].is_terisi),
        })

    master_standar_id = request.GET.get('standar')
    if master_standar_id == 'kosong':
        rows = tanpa_master_standar
    elif master_standar_id:
        rows = [r for r in all_rows if str(r['butir'].master_standar_id) == master_standar_id]
    else:
        rows = all_rows

    return render(request, 'ami_assessment/pengisian_detail.html', {
        'pengisian': pengisian,
        'rows': rows,
        'standar_nav': standar_nav,
        'standar_id': master_standar_id,
        'active_tab': 'self_assessment',
    })


@login_required
def jawaban_edit(request, butir_id):
    user_ami = _get_user_ami(request)
    siklus = Siklus.objects.filter(is_current=True).first()
    pengisian = _get_pengisian_untuk_user(user_ami, siklus) if siklus else None
    if pengisian is None:
        return redirect('self_assessment:pengisian_detail')

    butir = get_object_or_404(ButirPenilaian, pk=butir_id, siklus=siklus)

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
        butir_untuk_cakupan(
            ButirPenilaian.objects.filter(siklus=siklus, master_standar=butir.master_standar, is_aktif=True),
            pengisian.cakupan,
        ).order_by('no_urut'),
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
    siklus = Siklus.objects.filter(is_current=True).first()
    # get_or_create supaya konsisten dengan pengisian_detail/jawaban_edit --
    # sebelumnya pakai filter().first(), jadi upload gagal diam-diam kalau
    # auditee belum pernah membuka tab Self-Assessment dulu.
    pengisian = _get_pengisian_untuk_user(user_ami, siklus) if siklus else None

    if pengisian is None:
        messages.error(
            request,
            'Akun Anda belum terhubung ke profil AMI (prodi/fakultas) atau belum ada siklus AMI aktif.',
        )
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'upload'})

    if request.method == 'POST':
        form = DokumenBuktiForm(request.POST, request.FILES, siklus=siklus, cakupan=pengisian.cakupan)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.pengisian = pengisian
            obj.diunggah_oleh = user_ami
            obj.save()
            messages.success(request, f'Dokumen "{obj.nama_dokumen}" berhasil ditambahkan.')
            return redirect('self_assessment:upload_bukti')
    else:
        form = DokumenBuktiForm(siklus=siklus, cakupan=pengisian.cakupan)

    semua_dokumen = DokumenBukti.objects.filter(pengisian=pengisian).select_related('butir__standar', 'butir__master_standar')

    stats = {
        'total': semua_dokumen.count(),
        'terverifikasi': semua_dokumen.filter(status='terverifikasi').count(),
        'menunggu': semua_dokumen.filter(status__in=['belum_diverifikasi', 'menunggu_upm']).count(),
        'revisi': semua_dokumen.filter(status__in=['ditolak', 'perlu_revisi']).count(),
    }

    # Filter & pencarian
    dokumen_qs = semua_dokumen
    q = request.GET.get('q', '').strip()
    standar_id = request.GET.get('standar', '')
    status_filter = request.GET.get('status', '')
    format_filter = request.GET.get('format', '')

    if q:
        dokumen_qs = dokumen_qs.filter(nama_dokumen__icontains=q)
    if standar_id:
        dokumen_qs = dokumen_qs.filter(butir__master_standar_id=standar_id)
    if status_filter:
        dokumen_qs = dokumen_qs.filter(status=status_filter)
    if format_filter:
        dokumen_qs = dokumen_qs.filter(format=format_filter)

    dokumen_qs = dokumen_qs.order_by('-diunggah_pada')

    format_choices = semua_dokumen.exclude(format__isnull=True).exclude(format='').values_list(
        'format', flat=True,
    ).distinct().order_by('format')

    paginator = Paginator(dokumen_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ami_assessment/upload_bukti.html', {
        'form': form, 'page_obj': page_obj, 'stats': stats,
        'standar_list': MasterStandar.objects.order_by('no_urut'),
        'status_choices': DokumenBukti.STATUS_CHOICES,
        'format_choices': format_choices,
        'q': q, 'standar_id': standar_id, 'status_filter': status_filter, 'format_filter': format_filter,
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
        'pengisian__prodi__fakultas', 'pengisian__fakultas', 'butir',
    ).order_by('status', '-diunggah_pada')

    # UPM (bukan LP3M/superuser) hanya lihat dokumen dari prodi di fakultasnya
    # sendiri, atau Pengisian tingkat fakultas miliknya sendiri -- mencegah
    # UPM memvalidasi lintas fakultas yang bukan wewenangnya.
    is_pengawas_penuh = request.user.is_superuser or (user_ami and user_ami.is_lp3m)
    if not is_pengawas_penuh and user_ami and user_ami.is_upm and user_ami.fakultas_id:
        dokumen_qs = dokumen_qs.filter(
            Q(pengisian__prodi__fakultas_id=user_ami.fakultas_id) |
            Q(pengisian__fakultas_id=user_ami.fakultas_id),
        )

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
