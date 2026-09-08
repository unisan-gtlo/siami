# Seed RefEnumerasi + MasterStandar dari "telaah permen 39/ref-enumerasi.csv"
# (LP3M, lampiran MIGRASI-PERMEN-39-2025.md). Isi CSV di-inline di sini,
# bukan dibaca dari file saat runtime -- migration harus mandiri dan
# reversible tanpa bergantung pada berkas eksternal yang mungkin tidak ada
# di server produksi.
from django.db import migrations

REF_ENUMERASI = [
    # (kelompok, kode, nilai, domain_induk, keterangan)
    ('Domain', 'PDD', 'Pendidikan', None, 'Pasal 4 ayat (1) huruf a'),
    ('Domain', 'PNL', 'Penelitian', None, 'Pasal 4 ayat (1) huruf b'),
    ('Domain', 'PKM', 'Pengabdian kepada Masyarakat', None, 'Pasal 4 ayat (1) huruf c'),
    ('Domain', 'NAK', 'Nonakademik', None, 'Pasal 65 ayat (4)'),
    ('Kelompok Standar', 'L', 'Luaran', None, 'Diutamakan dalam pembobotan (Pasal 75 ayat 2)'),
    ('Kelompok Standar', 'P', 'Proses', None, None),
    ('Kelompok Standar', 'M', 'Masukan', None, None),
    ('Kelompok Standar', 'T', 'Tata Kelola SPMI', None, 'Butir atas sistem penjaminan mutu itu sendiri'),
    ('Metode Verifikasi', 'MV-1', 'Telaah Dokumen', None, 'Sumber triangulasi ke-1'),
    ('Metode Verifikasi', 'MV-2', 'Wawancara', None, 'Sumber triangulasi ke-2'),
    ('Metode Verifikasi', 'MV-3', 'Observasi Lapangan', None, 'Sumber triangulasi ke-3'),
    ('Metode Verifikasi', 'MV-4', 'Verifikasi PD Dikti', None, 'Pasal 66 ayat (1) — basis data utama'),
    ('Sumber Data', 'SD-1', 'PD Dikti', None, 'Tarik otomatis via API/feeder'),
    ('Sumber Data', 'SD-2', 'SIMAK / SIA UNISAN', None, None),
    ('Sumber Data', 'SD-3', 'Dokumen Prodi', None, None),
    ('Sumber Data', 'SD-4', 'Dokumen UPPS/Fakultas', None, None),
    ('Sumber Data', 'SD-5', 'Dokumen Universitas', None, None),
    ('Sumber Data', 'SD-6', 'Survei / Tracer Study', None, None),
    ('Tahap Audit', 'TA-1', 'Desk Evaluasi (Audit Sistem)', None, 'Bab V.2.3 Panduan AMI UNISAN'),
    ('Tahap Audit', 'TA-2', 'Audit Lapangan (Audit Kepatuhan)', None, 'Bab V.2.4 Panduan AMI UNISAN'),
    ('Tahap Audit', 'TA-3', 'Keduanya', None, None),
    ('Lapis Audit', 'LA-1', 'Kepatuhan SN Dikti', None, 'Ambang status Terakreditasi (Pasal 73/74 ayat 5)'),
    ('Lapis Audit', 'LA-2', 'Pelampauan (Unggul)', None, 'Melampaui SN Dikti (Pasal 73/74 ayat 6)'),
    ('Sasaran Auditee', 'AU-1', 'Program Studi', None, None),
    ('Sasaran Auditee', 'AU-2', 'UPPS / Fakultas', None, None),
    ('Sasaran Auditee', 'AU-3', 'Unit / Biro / Lembaga', None, None),
    ('Sasaran Auditee', 'AU-4', 'Universitas', None, None),
    ('Jenis Jawaban', 'JJ-1', 'Skala 0-4', None, 'Menggunakan rubrik'),
    ('Jenis Jawaban', 'JJ-2', 'Ya / Tidak', None, 'Ya = 4, Tidak = 0'),
    ('Jenis Jawaban', 'JJ-3', 'Numerik', None, 'Dibandingkan terhadap ambang pada indikator'),
    ('Jenis Jawaban', 'JJ-4', 'Persentase', None, None),
    ('Jenis Jawaban', 'JJ-5', 'Uraian + Bukti', None, 'Dinilai kualitatif oleh auditor'),
    ('Klasifikasi Temuan', 'KT-1', 'Sesuai (Conformity)', None, 'Skor 4'),
    ('Klasifikasi Temuan', 'KT-2', 'Observasi (OB)', None, 'Skor 3 — sesuai, berpotensi menurun'),
    ('Klasifikasi Temuan', 'KT-3', 'Ketidaksesuaian Minor (KTS Minor)', None, 'Skor 2'),
    ('Klasifikasi Temuan', 'KT-4', 'Ketidaksesuaian Mayor (KTS Mayor)', None, 'Skor 0-1, atau skor < 3 pada butir kritis'),
    ('Status Butir', 'ST-1', 'Draf', None, None),
    ('Status Butir', 'ST-2', 'Aktif', None, 'Terdistribusi ke auditee'),
    ('Status Butir', 'ST-3', 'Nonaktif', None, None),
    ('Status Butir', 'ST-4', 'Diarsipkan', None, 'Siklus terdahulu'),
]

MASTER_STANDAR = [
    # (kode, nama, domain_induk, keterangan/pasal, no_urut)
    ('STD-01', 'Standar Kompetensi Lulusan', 'Pendidikan / Luaran', 'Pasal 5 ayat (2), Pasal 6-10', 1),
    ('STD-02', 'Standar Proses Pembelajaran', 'Pendidikan / Proses', 'Pasal 5 ayat (3) huruf a, Pasal 11-25', 2),
    ('STD-03', 'Standar Penilaian', 'Pendidikan / Proses', 'Pasal 5 ayat (3) huruf b, Pasal 26-30', 3),
    ('STD-04', 'Standar Pengelolaan', 'Pendidikan / Proses', 'Pasal 5 ayat (3) huruf c, Pasal 31-39', 4),
    ('STD-05', 'Standar Isi', 'Pendidikan / Masukan', 'Pasal 5 ayat (4) huruf a, Pasal 40-45', 5),
    ('STD-06', 'Standar Dosen dan Tenaga Kependidikan', 'Pendidikan / Masukan', 'Pasal 5 ayat (4) huruf b, Pasal 46-47', 6),
    ('STD-07', 'Standar Sarana dan Prasarana', 'Pendidikan / Masukan', 'Pasal 5 ayat (4) huruf c, Pasal 48-50', 7),
    ('STD-08', 'Standar Pembiayaan', 'Pendidikan / Masukan', 'Pasal 5 ayat (4) huruf d, Pasal 51', 8),
    ('STD-09', 'Standar Luaran Penelitian', 'Penelitian / Luaran', 'Pasal 52-53', 9),
    ('STD-10', 'Standar Proses Penelitian', 'Penelitian / Proses', 'Pasal 54-56', 10),
    ('STD-11', 'Standar Masukan Penelitian', 'Penelitian / Masukan', 'Pasal 57', 11),
    ('STD-12', 'Standar Luaran PkM', 'PkM / Luaran', 'Pasal 58-59', 12),
    ('STD-13', 'Standar Proses PkM', 'PkM / Proses', 'Pasal 60-62', 13),
    ('STD-14', 'Standar Masukan PkM', 'PkM / Masukan', 'Pasal 63', 14),
    ('STD-15', 'Standar Pendidikan Tinggi yang Ditetapkan PT', 'Nonakademik / Tata Kelola SPMI', 'Pasal 64', 15),
    ('STD-16', 'Sistem Penjaminan Mutu Internal', 'Nonakademik / Tata Kelola SPMI', 'Pasal 67-69', 16),
    ('STD-17', 'Data dan Pelaporan PD Dikti', 'Nonakademik / Tata Kelola SPMI', 'Pasal 111-112', 17),
    ('STD-18', 'Kesiapan SPME / Akreditasi', 'Nonakademik / Tata Kelola SPMI', 'Pasal 70-83, Pasal 114-116', 18),
]


def seed(apps, schema_editor):
    RefEnumerasi = apps.get_model('ami_core', 'RefEnumerasi')
    MasterStandar = apps.get_model('ami_core', 'MasterStandar')

    for no_urut, (kelompok, kode, nilai, domain_induk, keterangan) in enumerate(REF_ENUMERASI, start=1):
        RefEnumerasi.objects.get_or_create(
            kelompok=kelompok, kode=kode,
            defaults=dict(nilai=nilai, domain_induk=domain_induk, keterangan=keterangan, no_urut=no_urut),
        )

    for kode, nama, domain_induk, keterangan, no_urut in MASTER_STANDAR:
        MasterStandar.objects.get_or_create(
            kode=kode,
            defaults=dict(nama=nama, domain_induk=domain_induk, keterangan=keterangan, no_urut=no_urut),
        )


def unseed(apps, schema_editor):
    RefEnumerasi = apps.get_model('ami_core', 'RefEnumerasi')
    MasterStandar = apps.get_model('ami_core', 'MasterStandar')
    RefEnumerasi.objects.filter(kelompok__in=[row[0] for row in REF_ENUMERASI]).delete()
    MasterStandar.objects.filter(kode__in=[row[0] for row in MASTER_STANDAR]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0008_masterstandar_butirpenilaian_butir_kritis_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
