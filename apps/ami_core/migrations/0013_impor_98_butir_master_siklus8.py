# T8 (MIGRASI-PERMEN-39-2025.md): impor 98 butir dari
# apps/ami_core/data/master_butir_ami_siklus8_2026.csv (disediakan LP3M,
# sitasi sudah mengacu Permendiktisaintek 39/2025).
#
# - Upsert berdasarkan (siklus, kode) -- BUKAN replace-all. Kode di CSV
#   ini semuanya berpola baru (AMI8.{DOM}.{KEL}.{NN}), sama sekali tidak
#   tumpang tindih dengan 58 kode lama (mis. "1a.1") dari seed 0003, jadi
#   ini murni insert baru -- 58 butir lama TIDAK disentuh/dihapus.
# - `standar` (FK lama, wajib diisi) diarahkan ke Standar kode='9'
#   ("Luaran dan Capaian Tridarma") untuk semua baris baru -- itu satu-
#   satunya baris Standar lama yang sengaja dikosongkan sejak 0003 karena
#   "tidak ada padanannya di sumber lama". Klasifikasi yang BENAR dan
#   presisi untuk butir-butir ini ada di `master_standar` (FK baru),
#   bukan di `standar` -- field itu sekadar pemenuhan constraint NOT NULL
#   warisan skema lama.
# - `jenis_input` (field lama, dipakai form self-assessment) diturunkan
#   dari `jenis_jawaban` (field baru, dipakai skor DE) karena CSV tidak
#   punya kolom terpisah untuk itu -- pemetaan: Skala 0-4 -> narasi
#   (auditee mengisi bukti naratif, DE yang beri skor), Ya/Tidak ->
#   pilihan, Numerik -> numerik, Persentase -> persentase.
from pathlib import Path

from django.db import migrations

CSV_PATH = Path(__file__).resolve().parent.parent / 'data' / 'master_butir_ami_siklus8_2026.csv'

DOMAIN_MAP = {
    'Pendidikan': 'PDD', 'Penelitian': 'PNL',
    'Pengabdian kepada Masyarakat': 'PKM', 'Nonakademik': 'NAK',
}
KELOMPOK_MAP = {'Luaran': 'L', 'Proses': 'P', 'Masukan': 'M', 'Tata Kelola SPMI': 'T'}
SUMBER_DATA_MAP = {
    'PD Dikti': 'SD-1', 'SIMAK/SIA': 'SD-2', 'Dokumen Prodi': 'SD-3',
    'Dokumen UPPS': 'SD-4', 'Dokumen Universitas': 'SD-5', 'Survei/Tracer': 'SD-6',
}
TAHAP_MAP = {'Desk Evaluasi': 'TA-1', 'Audit Lapangan': 'TA-2', 'Keduanya': 'TA-3'}
LAPIS_MAP = {'Kepatuhan SN Dikti': 'kepatuhan', 'Pelampauan (Unggul)': 'pelampauan'}
SASARAN_MAP = {'Program Studi': 'AU-1', 'UPPS/Fakultas': 'AU-2', 'Unit/Biro': 'AU-3', 'Universitas': 'AU-4'}
JENIS_JAWABAN_MAP = {'Skala 0-4': 'JJ-1', 'Ya/Tidak': 'JJ-2', 'Numerik': 'JJ-3', 'Persentase': 'JJ-4'}
JENIS_JAWABAN_KE_JENIS_INPUT = {'JJ-1': 'narasi', 'JJ-2': 'pilihan', 'JJ-3': 'numerik', 'JJ-4': 'persentase'}
METODE_MAP = {
    'Telaah Dokumen': 'MV-1', 'Wawancara': 'MV-2',
    'Observasi Lapangan': 'MV-3', 'Verifikasi PD Dikti': 'MV-4',
}


def split_multi(value):
    return [v.strip() for v in value.split(';') if v.strip()]


def seed(apps, schema_editor):
    import csv

    Siklus = apps.get_model('ami_core', 'Siklus')
    Standar = apps.get_model('ami_core', 'Standar')
    MasterStandar = apps.get_model('ami_core', 'MasterStandar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None or not CSV_PATH.exists():
        return

    standar_luaran = Standar.objects.filter(kode='9').first()
    master_standar_by_nama = {m.nama: m for m in MasterStandar.objects.all()}

    with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows, start=1):
        kode = row['Kode Butir'].strip()
        jenis_jawaban = JENIS_JAWABAN_MAP.get(row['Jenis Jawaban'].strip())
        dasar_hukum = split_multi(row['Dasar Hukum'])
        dokumen_bukti = [{'nama': n, 'wajib': True} for n in split_multi(row['Dokumen/Bukti Wajib'])]
        pernyataan = row['Pernyataan Butir'].strip()
        judul = pernyataan if len(pernyataan) <= 297 else pernyataan[:297] + '...'
        no_urut_suffix = kode.rsplit('.', 1)[-1]
        no_urut = int(no_urut_suffix) if no_urut_suffix.isdigit() else i

        ButirPenilaian.objects.update_or_create(
            siklus=siklus, kode=kode,
            defaults=dict(
                standar=standar_luaran,
                master_standar=master_standar_by_nama.get(row['Standar'].strip()),
                judul=judul,
                jenis_input=JENIS_JAWABAN_KE_JENIS_INPUT.get(jenis_jawaban, 'narasi'),
                bobot=int(row['Bobot']) if row['Bobot'].strip().isdigit() else 1,
                is_wajib=True,
                is_kuantitatif=jenis_jawaban in ('JJ-3', 'JJ-4'),
                rujukan_sn_dikti=dasar_hukum[0] if dasar_hukum else None,
                no_urut=no_urut,
                domain=DOMAIN_MAP.get(row['Domain'].strip()),
                kelompok_standar=KELOMPOK_MAP.get(row['Kelompok Standar'].strip()),
                sub_standar=row['Sub-standar'].strip() or None,
                pernyataan_butir=pernyataan,
                indikator_ketercapaian=row['Indikator Ketercapaian'].strip() or None,
                dasar_hukum=dasar_hukum or None,
                dokumen_bukti_wajib=dokumen_bukti or None,
                metode_verifikasi=[METODE_MAP[t] for t in split_multi(row['Metode Verifikasi']) if t in METODE_MAP] or None,
                sumber_data=SUMBER_DATA_MAP.get(row['Sumber Data'].strip()),
                tahap_audit=TAHAP_MAP.get(row['Tahap Audit'].strip()),
                lapis_audit=LAPIS_MAP.get(row['Lapis Audit'].strip(), 'kepatuhan'),
                sasaran_auditee=[SASARAN_MAP[t] for t in split_multi(row['Sasaran Auditee']) if t in SASARAN_MAP] or None,
                jenis_jawaban=jenis_jawaban,
                butir_kritis=row['Butir Kritis'].strip() == 'Ya',
                status='aktif' if row['Status'].strip() == 'Aktif' else 'draf',
                is_aktif=row['Status'].strip() == 'Aktif',
            ),
        )


def unseed(apps, schema_editor):
    import csv

    Siklus = apps.get_model('ami_core', 'Siklus')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None or not CSV_PATH.exists():
        return

    with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
        kode_list = [row['Kode Butir'].strip() for row in csv.DictReader(f)]

    ButirPenilaian.objects.filter(siklus=siklus, kode__in=kode_list).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0012_perbaiki_kelompok_standar_3c1'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
