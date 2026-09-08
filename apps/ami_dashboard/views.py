import datetime
from collections import Counter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.ami_core.models import RegulasiAcuan, Siklus
from apps.ami_master.models import Fakultas, Prodi
from apps.ami_assessment.models import Pengisian
from apps.ami_temuan.models import Temuan


@login_required
def lp3m_dashboard(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    is_pengawas = user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan)
    if not (request.user.is_superuser or is_pengawas):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_dashboard/forbidden.html', {'active_tab': 'dashboard'})

    siklus = Siklus.objects.filter(is_current=True).first()
    rows = []
    fakultas_rows = []
    pengisian_universitas = None
    if siklus:
        pengisian_by_prodi = {
            p.prodi_id: p for p in Pengisian.objects.filter(siklus=siklus, cakupan='prodi')
        }
        for prodi in Prodi.objects.filter(is_aktif=True).select_related('fakultas').order_by('fakultas__kode', 'nama'):
            pengisian = pengisian_by_prodi.get(prodi.id)
            rows.append({
                'prodi': prodi,
                'pengisian': pengisian,
            })

        pengisian_by_fakultas = {
            p.fakultas_id: p for p in Pengisian.objects.filter(siklus=siklus, cakupan='fakultas')
        }
        for fakultas in Fakultas.objects.filter(is_aktif=True).order_by('kode'):
            fakultas_rows.append({
                'fakultas': fakultas,
                'pengisian': pengisian_by_fakultas.get(fakultas.id),
            })

        pengisian_universitas = Pengisian.objects.filter(siklus=siklus, cakupan='universitas').first()

    total_prodi = len(rows)
    sudah_mulai = sum(1 for r in rows if r['pengisian'])
    selesai = sum(1 for r in rows if r['pengisian'] and r['pengisian'].status == 'completed')

    tenggat_peralihan = _hitung_tenggat_peralihan()
    distribusi_temuan, top_5_issue = _hitung_temuan_rektor(siklus)

    return render(request, 'ami_dashboard/dashboard.html', {
        'siklus': siklus,
        'rows': rows,
        'fakultas_rows': fakultas_rows,
        'pengisian_universitas': pengisian_universitas,
        'total_prodi': total_prodi,
        'sudah_mulai': sudah_mulai,
        'selesai': selesai,
        'tenggat_peralihan': tenggat_peralihan,
        'distribusi_temuan': distribusi_temuan,
        'top_5_issue': top_5_issue,
        'active_tab': 'dashboard',
    })


def _hitung_temuan_rektor(siklus):
    """Data untuk 2 chart Dashboard Rektor: distribusi Temuan per fakultas,
    dan top 5 isu (butir) paling sering muncul sebagai Temuan lintas prodi.
    Dihitung dari Temuan riil -- tidak ada data contoh/fiktif; kalau belum
    ada Temuan sama sekali, chart tampil kosong apa adanya."""
    if siklus is None:
        return {'labels': [], 'data': []}, []

    temuan_qs = Temuan.objects.filter(siklus=siklus).select_related(
        'pengisian__prodi__fakultas', 'pengisian__fakultas', 'butir',
    )

    fakultas_counter = Counter()
    for t in temuan_qs:
        if t.pengisian.cakupan == 'prodi' and t.pengisian.prodi_id and t.pengisian.prodi.fakultas_id:
            fakultas_counter[t.pengisian.prodi.fakultas.nama_singkat] += 1
        elif t.pengisian.cakupan == 'fakultas' and t.pengisian.fakultas_id:
            fakultas_counter[t.pengisian.fakultas.nama_singkat] += 1
        # cakupan universitas: institusi-wide, bukan milik satu fakultas -- tidak dihitung di sini.

    urut = fakultas_counter.most_common()
    distribusi_temuan = {
        'labels': [nama for nama, _ in urut],
        'data': [jumlah for _, jumlah in urut],
    }

    issue_counter = Counter()
    issue_label = {}
    for t in temuan_qs:
        if t.butir_id:
            issue_counter[t.butir_id] += 1
            issue_label[t.butir_id] = f'{t.butir.kode}'
    top_5_issue = [
        {'kode': issue_label[butir_id], 'jumlah': jumlah}
        for butir_id, jumlah in issue_counter.most_common(5)
    ]

    return distribusi_temuan, top_5_issue


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
