from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_assessment.models import JawabanButir
from apps.ami_core.models import ButirPenilaian

from .forms import DePenilaianForm
from .models import DePenilaian, DePenugasan


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

    butir_qs = ButirPenilaian.objects.filter(
        siklus=penugasan.siklus, is_aktif=True,
    ).select_related('standar')
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

    if request.method == 'POST':
        form = DePenilaianForm(request.POST, instance=penilaian)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.dinilai_pada = timezone.now()
            obj.save()
            messages.success(request, f'Penilaian butir {butir.kode} tersimpan.')
            return redirect('de:penugasan_detail', penugasan_id=penugasan.id)
    else:
        form = DePenilaianForm(instance=penilaian)

    return render(request, 'ami_de/penilaian_form.html', {
        'form': form, 'butir': butir, 'penugasan': penugasan, 'jawaban_auditee': jawaban_auditee,
        'active_tab': 'de',
    })
