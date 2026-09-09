from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_assessment.models import DokumenBukti, JawabanButir, Pengisian
from apps.ami_core.models import ButirPenilaian, Siklus, butir_untuk_cakupan
from apps.ami_user.views import ada_konflik_kepentingan

from .forms import DePenilaianForm, DePenugasanForm
from .models import DePenilaian, DePenugasan, hitung_klasifikasi


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


def _is_pengawas(request):
    user_ami = _get_user_ami(request)
    return request.user.is_superuser or (user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan))


@login_required
def penugasan_list(request):
    user_ami = _get_user_ami(request)
    if user_ami is None and not request.user.is_superuser:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI.')
        return render(request, 'ami_de/no_profile.html', {'active_tab': 'de'})

    if _is_pengawas(request):
        siklus = Siklus.objects.filter(is_current=True).first()
        penugasan_qs = DePenugasan.objects.filter(siklus=siklus).select_related(
            'pengisian__prodi', 'pengisian__fakultas', 'siklus', 'auditor__user',
        ).order_by('tenggat_de') if siklus else DePenugasan.objects.none()
        return render(request, 'ami_de/penugasan_list.html', {
            'penugasan_list': penugasan_qs, 'active_tab': 'de',
            'is_admin_view': True, 'siklus': siklus,
        })

    penugasan_qs = DePenugasan.objects.filter(auditor=user_ami).select_related(
        'pengisian__prodi', 'siklus',
    ).order_by('-siklus', 'tenggat_de')

    return render(request, 'ami_de/penugasan_list.html', {
        'penugasan_list': penugasan_qs, 'active_tab': 'de', 'is_admin_view': False,
    })


@login_required
def dashboard_saya(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or not user_ami.is_auditor_de:
        messages.error(request, 'Halaman ini hanya untuk Auditor Desk Evaluasi.')
        return render(request, 'ami_de/no_profile.html', {'active_tab': 'de'})

    siklus = Siklus.objects.filter(is_current=True).first()
    penugasan_qs = DePenugasan.objects.filter(auditor=user_ami, siklus=siklus).select_related(
        'pengisian__prodi', 'pengisian__fakultas',
    ) if siklus else DePenugasan.objects.none()

    aktif_qs = penugasan_qs.exclude(status__in=['selesai_de', 'difinalisasi', 'dibatalkan'])
    penugasan_list = list(penugasan_qs)
    progress_list = [
        round(p.butir_dinilai / p.total_butir * 100, 1) for p in penugasan_list if p.total_butir
    ]
    rata_progress = round(sum(progress_list) / len(progress_list), 1) if progress_list else 0

    return render(request, 'ami_de/dashboard.html', {
        'siklus': siklus, 'user_ami': user_ami,
        'total_penugasan': len(penugasan_list),
        'total_aktif': aktif_qs.count(),
        'rata_progress': rata_progress,
        'penugasan_terdekat': aktif_qs.order_by('tenggat_de')[:5],
        'active_tab': 'de',
    })


@login_required
def penugasan_create(request):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M.')
        return redirect('de:penugasan_list')

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None:
        messages.error(request, 'Tidak ada siklus AMI yang aktif. Aktifkan siklus dulu lewat Kelola Instrumen.')
        return redirect('de:penugasan_list')

    if request.method == 'POST':
        form = DePenugasanForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd['cakupan'] == 'prodi':
                pengisian, _ = Pengisian.objects.get_or_create(
                    siklus=siklus, cakupan='prodi', prodi=cd['prodi'],
                )
            elif cd['cakupan'] == 'fakultas':
                pengisian, _ = Pengisian.objects.get_or_create(
                    siklus=siklus, cakupan='fakultas', fakultas=cd['fakultas'],
                )
            else:
                pengisian, _ = Pengisian.objects.get_or_create(
                    siklus=siklus, cakupan='universitas',
                )

            try:
                DePenugasan.objects.create(
                    siklus=siklus, pengisian=pengisian, auditor=cd['auditor'],
                    role_dalam_tim=cd['role_dalam_tim'], sk_no=cd['sk_no'], sk_tgl=cd['sk_tgl'],
                    tgl_mulai_de=cd['tgl_mulai_de'], tenggat_de=cd['tenggat_de'],
                )
            except IntegrityError:
                messages.error(
                    request,
                    f'Auditor "{cd["auditor"]}" sudah ditugaskan ke "{pengisian.subjek}" untuk siklus ini.',
                )
            else:
                messages.success(request, f'Auditor "{cd["auditor"]}" berhasil ditugaskan ke "{pengisian.subjek}".')
                if ada_konflik_kepentingan(cd['auditor']):
                    messages.warning(
                        request,
                        f'Perhatian: "{cd["auditor"]}" punya penugasan DE lain di fakultasnya sendiri -- '
                        'periksa kembali prinsip crossover mandatory sebelum dilanjutkan.',
                    )
                return redirect('de:penugasan_list')
    else:
        form = DePenugasanForm()

    return render(request, 'ami_de/penugasan_create.html', {
        'form': form, 'siklus': siklus, 'active_tab': 'de',
    })


@login_required
def penugasan_detail(request, penugasan_id):
    user_ami = _get_user_ami(request)
    penugasan = get_object_or_404(DePenugasan, pk=penugasan_id, auditor=user_ami)

    butir_qs = butir_untuk_cakupan(
        ButirPenilaian.objects.filter(siklus=penugasan.siklus, is_aktif=True),
        penugasan.pengisian.cakupan,
    ).select_related('standar', 'master_standar')
    penilaian_by_butir = {
        p.butir_id: p for p in DePenilaian.objects.filter(penugasan=penugasan)
    }

    rows = [{'butir': b, 'penilaian': penilaian_by_butir.get(b.id)} for b in butir_qs]

    total = butir_qs.count()
    dinilai = sum(1 for r in rows if r['penilaian'] and r['penilaian'].skor is not None)
    if penugasan.total_butir != total or penugasan.butir_dinilai != dinilai:
        penugasan.total_butir = total
        penugasan.butir_dinilai = dinilai
        penugasan.butir_skor_1 = sum(1 for r in rows if r['penilaian'] and r['penilaian'].skor == 1)
        penugasan.butir_skor_0 = sum(1 for r in rows if r['penilaian'] and r['penilaian'].skor == 0)
        penugasan.save(update_fields=[
            'total_butir', 'butir_dinilai', 'butir_skor_1', 'butir_skor_0', 'updated_at',
        ])

    return render(request, 'ami_de/penugasan_detail.html', {
        'penugasan': penugasan, 'rows': rows, 'active_tab': 'de',
        'belum_dievaluasi': penugasan.total_butir - penugasan.butir_dinilai,
    })


@login_required
def penilaian_edit(request, penugasan_id, butir_id):
    user_ami = _get_user_ami(request)
    penugasan = get_object_or_404(DePenugasan, pk=penugasan_id, auditor=user_ami)
    butir = get_object_or_404(ButirPenilaian, pk=butir_id, siklus=penugasan.siklus)

    jawaban_auditee = JawabanButir.objects.filter(
        pengisian=penugasan.pengisian, butir=butir,
    ).first()

    penilaian, _ = DePenilaian.objects.get_or_create(
        penugasan=penugasan, butir=butir, defaults={'jawaban': jawaban_auditee},
    )

    dokumen_auditee = DokumenBukti.objects.filter(
        pengisian=penugasan.pengisian, butir=butir,
    ).select_related('diverifikasi_oleh__user')

    if penilaian.is_finalisasi:
        messages.info(
            request,
            f'Penilaian butir {butir.kode} sudah difinalisasi dan tidak bisa diubah lagi.',
        )
        return render(request, 'ami_de/penilaian_form.html', {
            'butir': butir, 'penugasan': penugasan, 'jawaban_auditee': jawaban_auditee,
            'dokumen_auditee': dokumen_auditee, 'penilaian': penilaian, 'readonly': True,
            'active_tab': 'de',
        })

    if request.method == 'POST':
        form = DePenilaianForm(request.POST, instance=penilaian)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.dinilai_pada = timezone.now()
            obj.klasifikasi = hitung_klasifikasi(obj.skor, butir.butir_kritis)
            if request.POST.get('action') == 'finalisasi':
                if obj.skor is None:
                    messages.error(request, 'Isi skor kesesuaian dulu sebelum finalisasi.')
                    return render(request, 'ami_de/penilaian_form.html', {
                        'form': form, 'butir': butir, 'penugasan': penugasan,
                        'jawaban_auditee': jawaban_auditee, 'dokumen_auditee': dokumen_auditee,
                        'active_tab': 'de',
                    })
                obj.is_draft = False
                obj.is_finalisasi = True
                obj.difinalisasi_pada = timezone.now()
                obj.save()
                messages.success(request, f'Penilaian butir {butir.kode} difinalisasi dan terkunci.')
            else:
                obj.is_draft = True
                obj.save()
                messages.success(request, f'Penilaian butir {butir.kode} tersimpan sebagai draft.')
            return redirect('de:penugasan_detail', penugasan_id=penugasan.id)
    else:
        form = DePenilaianForm(instance=penilaian)

    return render(request, 'ami_de/penilaian_form.html', {
        'form': form, 'butir': butir, 'penugasan': penugasan, 'jawaban_auditee': jawaban_auditee,
        'dokumen_auditee': dokumen_auditee,
        'active_tab': 'de',
    })
