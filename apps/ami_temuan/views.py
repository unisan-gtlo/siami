import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import Siklus
from apps.ami_de.models import DePenilaian

from .forms import FvtbUpdateForm, TemuanFromDePenilaianForm
from .models import Fvtb, Temuan

TENGGAT_HARI = {'KTB': 30, 'KTS': 60, 'OB': 90}


@login_required
def temuan_list(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_temuan/no_profile.html', {'active_tab': 'temuan'})

    siklus = Siklus.objects.filter(is_current=True).first()
    temuan_qs = Temuan.objects.filter(
        siklus=siklus, pengisian__prodi=user_ami.prodi,
    ).select_related('butir').prefetch_related('fvtb_set').order_by('klasifikasi', '-created_at')

    stats = {kode: temuan_qs.filter(klasifikasi=kode).count() for kode in ('KTB', 'KTS', 'OB', 'BP')}

    return render(request, 'ami_temuan/temuan_list.html', {
        'temuan_list': temuan_qs, 'stats': stats, 'active_tab': 'temuan',
    })


@login_required
def fvtb_update(request, fvtb_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    fvtb = get_object_or_404(Fvtb, pk=fvtb_id, pic=user_ami)
    progress_sebelum = fvtb.progress_persen

    if request.method == 'POST':
        form = FvtbUpdateForm(request.POST, instance=fvtb)
        if form.is_valid():
            # form.is_valid() sudah menulis field yang dibersihkan ke fvtb
            # (instance yang sama) lewat _post_clean() -- progress_sebelum
            # WAJIB dibaca sebelum baris ini, bukan sesudah is_valid().
            obj = form.save(commit=False)
            obj.update_pada = timezone.now()
            if obj.progress_persen >= 100:
                obj.status = 'check'
            obj.save()
            obj.progress_log_set.create(
                progress_sebelum=progress_sebelum,
                progress_sesudah=obj.progress_persen,
                update_text=obj.update_terakhir or '',
                diupdate_oleh=user_ami,
            )
            messages.success(request, 'Progress tindak lanjut tersimpan.')
            return redirect('temuan:temuan_list')
    else:
        form = FvtbUpdateForm(instance=fvtb)

    return render(request, 'ami_temuan/fvtb_update.html', {
        'form': form, 'fvtb': fvtb, 'active_tab': 'temuan',
    })


@login_required
def temuan_create_from_de(request, penilaian_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    penilaian = get_object_or_404(
        DePenilaian, pk=penilaian_id, penugasan__auditor=user_ami,
    )

    if not penilaian.is_finalisasi:
        messages.error(request, 'Finalisasi penilaian ini dulu sebelum membuat Temuan.')
        return redirect('de:penugasan_detail', penugasan_id=penilaian.penugasan_id)

    existing = Temuan.objects.filter(de_penilaian=penilaian).first()
    if existing:
        messages.info(request, 'Temuan untuk penilaian ini sudah pernah dibuat.')
        return redirect('temuan:temuan_list')

    if request.method == 'POST':
        form = TemuanFromDePenilaianForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.siklus = penilaian.penugasan.siklus
            obj.pengisian = penilaian.penugasan.pengisian
            obj.butir = penilaian.butir
            obj.sumber_temuan = 'de'
            obj.de_penilaian = penilaian
            obj.dilaporkan_oleh = user_ami
            seq = Temuan.objects.filter(siklus=obj.siklus).count() + 1
            obj.no_temuan = f'T-S{obj.siklus.no_siklus}-{seq:03d}'
            obj.save()
            messages.success(request, f'Temuan {obj.no_temuan} berhasil dibuat.')
            return redirect('temuan:temuan_list')
    else:
        klasifikasi = penilaian.klasifikasi or ('BP' if penilaian.skor == 1 else 'OB')
        tenggat = None
        if klasifikasi in TENGGAT_HARI:
            tenggat = timezone.now().date() + datetime.timedelta(days=TENGGAT_HARI[klasifikasi])
        form = TemuanFromDePenilaianForm(initial={
            'klasifikasi': klasifikasi,
            'judul': f'{penilaian.butir.kode} — {penilaian.butir.judul}',
            'deskripsi_problem': penilaian.plor_problem or '',
            'lokasi_temuan': penilaian.plor_location or '',
            'standar_dilanggar': penilaian.plor_objective or '',
            'bukti_referensi': penilaian.plor_reference or '',
            'tenggat_tindak_lanjut': tenggat,
            'layak_replikasi': klasifikasi == 'BP',
        })

    return render(request, 'ami_temuan/temuan_from_de_form.html', {
        'form': form, 'penilaian': penilaian, 'active_tab': 'de',
    })
