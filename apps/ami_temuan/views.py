import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import Siklus
from apps.ami_de.models import DePenilaian, hitung_klasifikasi

from .forms import FvtbUpdateForm, FvtbVerifyForm, TemuanFromDePenilaianForm
from .models import Fvtb, Temuan

# Permendiktisaintek 39/2025 (spesifikasi-modul-kelola-instrumen.md bagian 3):
# KTS Mayor = PTK segera, tenggat maksimal 1 bulan; KTS Minor = PTK, tenggat
# maksimal 3 bulan setelah RTM. OB/Sesuai tidak menghasilkan tenggat PTK.
TENGGAT_HARI = {'KTS_MAYOR': 30, 'KTS_MINOR': 90}


def _is_monitor(user, user_ami):
    return user.is_superuser or (user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan))


@login_required
def temuan_list(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_temuan/no_profile.html', {'active_tab': 'temuan'})

    siklus = Siklus.objects.filter(is_current=True).first()
    base_qs = Temuan.objects.filter(
        siklus=siklus, pengisian__prodi=user_ami.prodi,
    ).select_related('butir').prefetch_related('fvtb_set')

    stats = {
        'KTS_MAYOR': base_qs.filter(klasifikasi__in=['KTS_MAYOR', 'KTB']).count(),
        'KTS_MINOR': base_qs.filter(klasifikasi__in=['KTS_MINOR', 'KTS']).count(),
        'OB': base_qs.filter(klasifikasi='OB').count(),
        'SESUAI': base_qs.filter(klasifikasi__in=['SESUAI', 'BP']).count(),
    }

    total = base_qs.count()
    closed = base_qs.filter(status='closed').count()
    persentase_selesai = round(closed * 100 / total) if total else 0

    klasifikasi_filter = request.GET.get('klasifikasi', '')
    status_filter = request.GET.get('status', '')
    tahap_filter = request.GET.get('tahap', '')

    temuan_qs = base_qs
    if klasifikasi_filter:
        temuan_qs = temuan_qs.filter(klasifikasi=klasifikasi_filter)
    if status_filter:
        temuan_qs = temuan_qs.filter(status=status_filter)
    if tahap_filter:
        temuan_qs = temuan_qs.filter(sumber_temuan=tahap_filter)
    temuan_qs = temuan_qs.order_by('klasifikasi', '-created_at')

    return render(request, 'ami_temuan/temuan_list.html', {
        'temuan_list': temuan_qs, 'stats': stats, 'active_tab': 'temuan',
        'total': total, 'closed': closed, 'persentase_selesai': persentase_selesai,
        'klasifikasi_choices': Temuan._meta.get_field('klasifikasi').choices,
        'status_choices': Temuan._meta.get_field('status').choices,
        'tahap_choices': Temuan._meta.get_field('sumber_temuan').choices,
        'klasifikasi_filter': klasifikasi_filter, 'status_filter': status_filter, 'tahap_filter': tahap_filter,
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
        klasifikasi = penilaian.klasifikasi or hitung_klasifikasi(penilaian.skor, penilaian.butir.butir_kritis)
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
            'layak_replikasi': klasifikasi == 'SESUAI',
        })

    return render(request, 'ami_temuan/temuan_from_de_form.html', {
        'form': form, 'penilaian': penilaian, 'active_tab': 'de',
    })


@login_required
def fvtb_dashboard(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    is_monitor = _is_monitor(request.user, user_ami)

    if user_ami is None and not request.user.is_superuser:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI.')
        return render(request, 'ami_temuan/no_profile.html', {'active_tab': 'tindak_lanjut'})

    siklus = Siklus.objects.filter(is_current=True).first()
    qs = Fvtb.objects.filter(temuan__siklus=siklus).select_related(
        'temuan__butir', 'temuan__pengisian__prodi', 'pic__user',
    ).order_by('tenggat_selesai')

    if not is_monitor:
        qs = qs.filter(pic=user_ami)

    today = timezone.now().date()
    aktif_qs = qs.exclude(status='closed')
    terlambat_qs = aktif_qs.filter(tenggat_selesai__lt=today)
    mendekati_qs = aktif_qs.filter(
        tenggat_selesai__gte=today, tenggat_selesai__lte=today + datetime.timedelta(days=7),
    )
    total_aktif = aktif_qs.count()
    terlambat_count = terlambat_qs.count()
    mendekati_count = mendekati_qs.count()
    tepat_waktu_count = total_aktif - terlambat_count - mendekati_count

    terlambat_ids = set(terlambat_qs.values_list('id', flat=True))
    mendekati_ids = set(mendekati_qs.values_list('id', flat=True))

    rows = [{
        'fvtb': f,
        'is_terlambat': f.id in terlambat_ids,
        'is_mendekati': f.id in mendekati_ids,
        'is_pic': user_ami is not None and f.pic_id == user_ami.id,
    } for f in qs]

    pdca = {kode: aktif_qs.filter(status=kode).count() for kode in ('plan', 'do', 'check', 'act')}

    return render(request, 'ami_temuan/fvtb_dashboard.html', {
        'rows': rows,
        'stats': {
            'total_aktif': total_aktif, 'tepat_waktu': tepat_waktu_count,
            'mendekati_deadline': mendekati_count, 'terlambat': terlambat_count,
        },
        'pdca': pdca,
        'is_monitor': is_monitor,
        'active_tab': 'tindak_lanjut',
    })


@login_required
def fvtb_detail(request, fvtb_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    is_monitor = _is_monitor(request.user, user_ami)
    fvtb = get_object_or_404(Fvtb, pk=fvtb_id)

    if not is_monitor and (user_ami is None or fvtb.pic_id != user_ami.id):
        messages.error(request, 'Anda tidak punya akses ke F-VTB ini.')
        return redirect('temuan:fvtb_dashboard')

    return render(request, 'ami_temuan/fvtb_detail.html', {
        'fvtb': fvtb, 'active_tab': 'tindak_lanjut',
    })


@login_required
def fvtb_verify(request, fvtb_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    if not _is_monitor(request.user, user_ami):
        messages.error(request, 'Verifikasi F-VTB hanya untuk LP3M/Pimpinan.')
        return redirect('temuan:fvtb_dashboard')

    fvtb = get_object_or_404(Fvtb, pk=fvtb_id)

    if fvtb.status != 'check':
        messages.info(request, 'F-VTB ini belum berada di tahap Check (menunggu PIC menyelesaikan progress).')
        return redirect('temuan:fvtb_dashboard')

    if request.method == 'POST':
        form = FvtbVerifyForm(request.POST, instance=fvtb)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.sudah_diverifikasi = True
            obj.verifikator = user_ami
            obj.diverifikasi_pada = timezone.now()
            obj.status = 'act'
            obj.save()
            messages.success(request, f'{obj.no_fvtb or "F-VTB"} berhasil diverifikasi.')
            return redirect('temuan:fvtb_dashboard')
    else:
        form = FvtbVerifyForm(instance=fvtb)

    return render(request, 'ami_temuan/fvtb_verify.html', {
        'form': form, 'fvtb': fvtb, 'active_tab': 'tindak_lanjut',
    })
