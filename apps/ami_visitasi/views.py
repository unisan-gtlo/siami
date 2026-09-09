from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.ami_core.models import Siklus

from .models import Visitasi, VisitasiAnggota


@login_required
def dashboard_saya(request):
    """Ringkasan visitasi yang ditugaskan ke auditor ini -- READ ONLY.
    Sengaja tidak ada aksi edit (isi agenda/notulen/BA/konfirmasi kehadiran
    sbg ketua tim) di halaman ini; itu bagian dari gap fitur auditor
    visitasi yang lebih besar dan ditunda terpisah."""
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or not user_ami.is_auditor_visitasi:
        messages.error(request, 'Halaman ini hanya untuk Auditor Visitasi.')
        return render(request, 'ami_visitasi/no_profile.html', {'active_tab': 'visitasi'})

    siklus = Siklus.objects.filter(is_current=True).first()
    anggota_qs = VisitasiAnggota.objects.filter(
        user=user_ami, visitasi__siklus=siklus,
    ).select_related(
        'visitasi__pengisian__prodi', 'visitasi__pengisian__fakultas', 'visitasi',
    ) if siklus else VisitasiAnggota.objects.none()

    anggota_list = list(anggota_qs)
    aktif_list = [a for a in anggota_list if a.visitasi.status not in ('selesai', 'closing_done', 'dibatalkan')]
    aktif_list.sort(key=lambda a: a.visitasi.tgl_visitasi)

    return render(request, 'ami_visitasi/dashboard.html', {
        'siklus': siklus,
        'total_visitasi': len(anggota_list),
        'total_aktif': len(aktif_list),
        'visitasi_terdekat': aktif_list[:5],
        'active_tab': 'visitasi',
    })


@login_required
def visitasi_saya(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_visitasi/no_profile.html', {'active_tab': 'visitasi'})

    siklus = Siklus.objects.filter(is_current=True).first()
    visitasi = Visitasi.objects.filter(
        siklus=siklus, pengisian__prodi=user_ami.prodi,
    ).select_related('ketua_tim__user', 'notulis__user').prefetch_related(
        'anggota_set__user__user', 'agenda_set__pic__user',
    ).first()

    return render(request, 'ami_visitasi/visitasi_detail.html', {
        'visitasi': visitasi, 'active_tab': 'visitasi',
    })


@login_required
def konfirmasi_kehadiran(request, visitasi_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    visitasi = Visitasi.objects.filter(pk=visitasi_id, pengisian__prodi=user_ami.prodi).first() \
        if user_ami else None
    if visitasi is None:
        messages.error(request, 'Visitasi tidak ditemukan.')
        return redirect('visitasi:visitasi_saya')

    if request.method == 'POST':
        visitasi.konfirmasi_status = 'dikonfirmasi'
        visitasi.konfirmasi_pada = timezone.now()
        visitasi.save(update_fields=['konfirmasi_status', 'konfirmasi_pada', 'updated_at'])
        messages.success(request, 'Kehadiran visitasi berhasil dikonfirmasi.')

    return redirect('visitasi:visitasi_saya')
