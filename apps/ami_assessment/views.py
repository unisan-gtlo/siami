from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import ButirPenilaian, Siklus

from .forms import DokumenBuktiForm, JawabanButirForm
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

    rows = []
    for butir in butir_qs:
        rows.append({
            'butir': butir,
            'jawaban': jawaban_by_butir.get(butir.id),
        })

    total = butir_qs.count()
    terisi = sum(1 for r in rows if r['jawaban'] and r['jawaban'].is_terisi)
    if pengisian.total_butir != total or pengisian.butir_terisi != terisi:
        pengisian.total_butir = total
        pengisian.butir_terisi = terisi
        pengisian.save(update_fields=['total_butir', 'butir_terisi', 'updated_at'])

    return render(request, 'ami_assessment/pengisian_detail.html', {
        'pengisian': pengisian,
        'rows': rows,
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
        form = JawabanButirForm(request.POST, instance=jawaban)
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
        form = JawabanButirForm(instance=jawaban)

    return render(request, 'ami_assessment/jawaban_form.html', {
        'form': form, 'butir': butir, 'pengisian': pengisian,
        'active_tab': 'self_assessment',
    })


@login_required
def upload_bukti(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_assessment/no_profile.html', {'active_tab': 'upload'})

    siklus = Siklus.objects.filter(is_current=True).first()
    pengisian = Pengisian.objects.filter(siklus=siklus, prodi=user_ami.prodi).first()

    if request.method == 'POST':
        form = DokumenBuktiForm(request.POST, request.FILES, siklus=siklus)
        if form.is_valid():
            if pengisian is None:
                messages.error(request, 'Belum ada self-assessment untuk siklus ini.')
                return redirect('self_assessment:upload_bukti')
            obj = form.save(commit=False)
            obj.pengisian = pengisian
            obj.diunggah_oleh = user_ami
            obj.save()
            messages.success(request, f'Dokumen "{obj.nama_dokumen}" berhasil ditambahkan.')
            return redirect('self_assessment:upload_bukti')
    else:
        form = DokumenBuktiForm(siklus=siklus)

    dokumen_list = DokumenBukti.objects.filter(pengisian=pengisian).select_related('butir') if pengisian else []

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
