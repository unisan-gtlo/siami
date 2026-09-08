import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.ami_core.models import RegulasiAcuan, Siklus
from apps.ami_master.models import Prodi
from apps.ami_assessment.models import Pengisian


@login_required
def lp3m_dashboard(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    is_pengawas = user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan)
    if not (request.user.is_superuser or is_pengawas):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_dashboard/forbidden.html', {'active_tab': 'dashboard'})

    siklus = Siklus.objects.filter(is_current=True).first()
    rows = []
    if siklus:
        pengisian_by_prodi = {
            p.prodi_id: p for p in Pengisian.objects.filter(siklus=siklus)
        }
        for prodi in Prodi.objects.filter(is_aktif=True).select_related('fakultas').order_by('fakultas__kode', 'nama'):
            pengisian = pengisian_by_prodi.get(prodi.id)
            rows.append({
                'prodi': prodi,
                'pengisian': pengisian,
            })

    total_prodi = len(rows)
    sudah_mulai = sum(1 for r in rows if r['pengisian'])
    selesai = sum(1 for r in rows if r['pengisian'] and r['pengisian'].status == 'completed')

    tenggat_peralihan = _hitung_tenggat_peralihan()

    return render(request, 'ami_dashboard/dashboard.html', {
        'siklus': siklus,
        'rows': rows,
        'total_prodi': total_prodi,
        'sudah_mulai': sudah_mulai,
        'selesai': selesai,
        'tenggat_peralihan': tenggat_peralihan,
        'active_tab': 'dashboard',
    })


def _hitung_tenggat_peralihan():
    """Panel pemantauan tenggat Ketentuan Peralihan Permendiktisaintek 39/2025
    (Pasal 113-116). Tanggal batas dihitung dari tanggal_undang RegulasiAcuan,
    bukan hardcode -- lihat MIGRASI-PERMEN-39-2025.md Tugas T7."""
    permen_39 = RegulasiAcuan.objects.filter(kode='PERMEN_39_2025').first()
    if not permen_39 or not permen_39.tanggal_undang:
        return None

    today = timezone.now().date()
    tanggal_undang = permen_39.tanggal_undang
    batas_1_tahun = tanggal_undang + datetime.timedelta(days=365)
    batas_2_tahun = tanggal_undang + datetime.timedelta(days=730)

    belum_terakreditasi = Prodi.objects.filter(
        is_aktif=True, status_akreditasi='tidak_terakreditasi',
    ).select_related('fakultas').order_by('fakultas__kode', 'nama')

    prodi_dengan_tanggal_operasi = Prodi.objects.filter(
        is_aktif=True, tanggal_mulai_beroperasi__isnull=False,
    ).select_related('fakultas').order_by('tanggal_mulai_beroperasi')
    per_prodi_rows = []
    for p in prodi_dengan_tanggal_operasi:
        batas = p.tanggal_mulai_beroperasi + datetime.timedelta(days=730)
        per_prodi_rows.append({'prodi': p, 'batas': batas, 'terlambat': batas < today})

    total_prodi_aktif = Prodi.objects.filter(is_aktif=True).count()

    return {
        'tanggal_undang': tanggal_undang,
        'batas_1_tahun': batas_1_tahun,
        'sisa_hari_1_tahun': (batas_1_tahun - today).days,
        'sisa_hari_1_tahun_abs': abs((batas_1_tahun - today).days),
        'batas_2_tahun': batas_2_tahun,
        'sisa_hari_2_tahun': (batas_2_tahun - today).days,
        'belum_terakreditasi': belum_terakreditasi,
        'per_prodi_rows': per_prodi_rows,
        'total_prodi_aktif': total_prodi_aktif,
        'prodi_tanpa_tanggal_operasi': total_prodi_aktif - len(per_prodi_rows),
    }
