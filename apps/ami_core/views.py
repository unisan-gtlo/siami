from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ButirPenilaianForm
from .models import ButirPenilaian, Siklus, Standar


@login_required
def home(request):
    """Arahkan ke halaman yang relevan sesuai role -- bukan selalu ke
    Self-Assessment, karena LP3M/Pimpinan/auditor tidak (dan sebaiknya
    tidak) punya prodi sendiri, jadi Self-Assessment justru menolak mereka."""
    user_ami = getattr(request.user, 'ami_profile', None)

    if request.user.is_superuser or (user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan)):
        return redirect('dashboard:lp3m')
    if user_ami and user_ami.is_auditor_de:
        return redirect('de:penugasan_list')
    if user_ami and user_ami.is_auditor_visitasi:
        return redirect('visitasi:visitasi_saya')
    if user_ami and user_ami.prodi_id:
        return redirect('self_assessment:pengisian_detail')

    messages.info(
        request,
        'Akun Anda belum terhubung ke role/prodi manapun di AMI. Hubungi LP3M/admin.',
    )
    return render(request, 'ami_core/no_role.html')


def _is_pengawas(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    return request.user.is_superuser or (user_ami and user_ami.is_lp3m)


@login_required
def butir_list(request):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M.')
        return render(request, 'ami_core/forbidden.html', {'active_tab': 'instrumen'})

    siklus = Siklus.objects.filter(is_current=True).first()
    butir_qs = ButirPenilaian.objects.filter(siklus=siklus).select_related('standar').order_by(
        'standar__no_urut', 'no_urut',
    ) if siklus else ButirPenilaian.objects.none()

    per_standar = []
    if siklus:
        for standar in Standar.objects.order_by('no_urut'):
            butir_standar = [b for b in butir_qs if b.standar_id == standar.id]
            per_standar.append({'standar': standar, 'butir': butir_standar, 'count': len(butir_standar)})

    return render(request, 'ami_core/butir_list.html', {
        'siklus': siklus, 'per_standar': per_standar, 'total_butir': butir_qs.count(),
        'active_tab': 'instrumen',
    })


@login_required
def butir_create(request):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M.')
        return redirect('instrumen:butir_list')

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None:
        messages.error(request, 'Tidak ada siklus AMI yang aktif.')
        return redirect('instrumen:butir_list')

    if request.method == 'POST':
        form = ButirPenilaianForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.siklus = siklus
            obj.save()
            messages.success(request, f'Butir {obj.kode} berhasil ditambahkan.')
            return redirect('instrumen:butir_list')
    else:
        form = ButirPenilaianForm()

    return render(request, 'ami_core/butir_form.html', {
        'form': form, 'siklus': siklus, 'active_tab': 'instrumen',
    })


@login_required
def butir_edit(request, butir_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M.')
        return redirect('instrumen:butir_list')

    butir = get_object_or_404(ButirPenilaian, pk=butir_id)

    if request.method == 'POST':
        form = ButirPenilaianForm(request.POST, instance=butir)
        if form.is_valid():
            form.save()
            messages.success(request, f'Butir {butir.kode} berhasil diperbarui.')
            return redirect('instrumen:butir_list')
    else:
        form = ButirPenilaianForm(instance=butir)

    return render(request, 'ami_core/butir_form.html', {
        'form': form, 'butir': butir, 'siklus': butir.siklus, 'active_tab': 'instrumen',
    })


@login_required
def butir_delete(request, butir_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M.')
        return redirect('instrumen:butir_list')

    butir = get_object_or_404(ButirPenilaian, pk=butir_id)

    if request.method == 'POST':
        kode = butir.kode
        try:
            butir.delete()
            messages.success(request, f'Butir {kode} berhasil dihapus.')
        except ProtectedError:
            messages.error(
                request,
                f'Butir {kode} tidak bisa dihapus karena sudah punya jawaban/penilaian '
                'tersimpan. Nonaktifkan saja lewat "Ubah" jika tidak ingin dipakai lagi.',
            )
        return redirect('instrumen:butir_list')

    return render(request, 'ami_core/butir_confirm_delete.html', {
        'butir': butir, 'active_tab': 'instrumen',
    })
