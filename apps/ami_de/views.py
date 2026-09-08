from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_assessment.models import DokumenBukti, JawabanButir
from apps.ami_core.models import ButirPenilaian, butir_untuk_cakupan

from .forms import DePenilaianForm
from .models import DePenilaian, DePenugasan, hitung_klasifikasi


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


@login_required
def penugasan_list(request):
    user_ami = _get_user_ami(request)
    if user_ami is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI.')
        return render(request, 'ami_de/no_profile.html', {'active_tab': 'de'})

    penugasan_qs = DePenugasan.objects.filter(auditor=user_ami).select_related(
        'pengisian__prodi', 'siklus',
    ).order_by('-siklus', 'tenggat_de')

    return render(request, 'ami_de/penugasan_list.html', {
        'penugasan_list': penugasan_qs, 'active_tab': 'de',
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
