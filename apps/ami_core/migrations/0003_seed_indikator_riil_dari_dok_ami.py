# Data diambil dari "dok ami/nama indikator_folder bukti.docx" -- daftar
# indikator asli UNISAN (kode + nama), BUKAN instrumen self-assessment
# lengkap (tidak ada definisi/jenis_input/target IKU per butir di sumbernya).
# jenis_input diseragamkan 'narasi' sebagai default aman; LP3M WAJIB
# melengkapi/menyesuaikan tiap butir lewat halaman Kelola Instrumen
# (/instrumen/) begitu instrumen resminya siap -- ini cuma titik awal,
# bukan instrumen final.
#
# Sumber pakai struktur "7 Kriteria" (Kriteria 7 menggabung Penelitian +
# Pengabdian), berbeda dari 9 Standar SN-Dikti yang sudah di-seed di
# migrasi 0002. Pemetaan: Kriteria 1-6 -> Standar 1-6 apa adanya;
# Kriteria 7a (Penelitian) -> Standar 7; Kriteria 7b (PKM) -> Standar 8.
# Standar 9 (Luaran) sengaja dikosongkan -- tidak ada padanannya di sumber.
#
# Sumber punya kode "3a.1" dua kali (baris ke-2 kemungkinan typo untuk
# "3a.2" -- isinya beda topik dari 3a.1 pertama). Diperbaiki jadi 3a.2
# di sini supaya tidak bentrok dengan unique constraint (siklus, kode).
from django.db import migrations

# (standar_kode, [(kode, judul), ...])
INDIKATOR_PER_STANDAR = [
    ('1', [
        ('1a.1', 'Misi — pencapaian'),
        ('1a.2', 'Misi — pelibatan pemangku kepentingan'),
        ('1a.3', 'Misi — evaluasi'),
        ('1a.4', 'Misi — pedoman'),
        ('1b.1', 'Visi — pencapaian'),
        ('1b.2', 'Visi — jelas, realistis, kredibel'),
        ('1b.3', 'Visi — standar kinerja'),
        ('1b.4', 'Visi — evaluasi'),
        ('1b.5', 'Visi — pedoman'),
        ('1c.1', 'Tujuan — pencapaian dan evaluasi'),
        ('1c.2', 'Sasaran — pencapaian dan evaluasi'),
        ('1c.3', 'Tujuan & sasaran — upaya dan tingkat pencapaian'),
        ('1d.1', 'Strategi — implementasi'),
        ('1d.2', 'Strategi — integrasi manajemen risiko'),
        ('1d.3', 'Strategi — pelibatan pemangku kepentingan'),
    ]),
    ('2', [
        ('2a.1', 'Tata pamong — struktur'),
        ('2a.2', 'Tata pamong — pengawasan, sinergi'),
        ('2b.1', 'Tata kelola — pelaksanaan 5 Pilar'),
        ('2b.2', 'Tata kelola — 3E, akuntabilitas'),
        ('2b.3', 'Tata kelola — implementasi SPMI'),
    ]),
    ('3', [
        ('3a.1', 'Mahasiswa — penerimaan'),
        ('3a.2', 'Mahasiswa — inklusif, afirmatif, adil, merata'),
        ('3b.1', 'Layanan akademik — penggunaan modalitas dan pedagogi'),
        ('3b.2', 'Layanan akademik — penggunaan unit kegiatan mahasiswa'),
        ('3c.1', 'Kinerja akademik — kemampuan'),
        ('3d.1', 'Kesejahteraan mahasiswa — layanan fisik, mental'),
        ('3d.2', 'Kesejahteraan mahasiswa — layanan olahraga, kesenian, kesehatan'),
        ('3d.3', 'Kesejahteraan mahasiswa — kebijakan tindak diskriminasi'),
        ('3e.1', 'Karir mahasiswa — program karir'),
    ]),
    ('4', [
        ('4a.1', 'Dosen — kecukupan'),
        ('4a.2', 'Dosen — penugasan'),
        ('4a.3', 'Dosen — beban kerja'),
        ('4b.1', 'Pengelolaan dosen — rencana, pengembangan'),
        ('4b.2', 'Pengelolaan dosen — dukungan'),
        ('4b.3', 'Pengelolaan dosen — evaluasi'),
        ('4c.1', 'Tenaga kependidikan — kecukupan'),
        ('4c.2', 'Tenaga kependidikan — kualifikasi'),
        ('4d.1', 'Pengelolaan tendik — rencana'),
        ('4d.2', 'Pengelolaan tendik — pengembangan'),
    ]),
    ('5', [
        ('5a.1', 'Keuangan — 4 Pilar'),
        ('5a.2', 'Keuangan — usaha keberlanjutan'),
        ('5b.1', 'Sarana — penyediaan, pengelolaan, pengembangan'),
        ('5b.2', 'Sarana — standar K4, gender, difabel'),
    ]),
    ('6', [
        ('6a.1', 'Kurikulum — peta, CPL'),
        ('6a.2', 'Kurikulum — implementasi'),
        ('6a.3', 'Kurikulum — materi, metode'),
        ('6a.4', 'Kurikulum — evaluasi'),
        ('6b.1', 'Jaminan pembelajaran — pengukuran langsung'),
        ('6b.2', 'Jaminan pembelajaran — pengukuran tidak langsung'),
        ('6b.3', 'Jaminan pembelajaran — intervensi'),
    ]),
    ('7', [
        ('7a.1', 'Penelitian — perencanaan'),
        ('7a.2', 'Penelitian — kegiatan dan hasilnya'),
        ('7a.3', 'Penelitian — kerjasama'),
        ('7a.4', 'Penelitian — kinerja dosen'),
    ]),
    ('8', [
        ('7b.1', 'PKM — perencanaan'),
        ('7b.2', 'PKM — kegiatan dan hasilnya/kontribusi'),
        ('7b.3', 'PKM — kerjasama'),
        ('7b.4', 'PKM — kinerja dosen'),
    ]),
]

PANDUAN_DEFAULT = (
    'Kumpulkan bukti pendukung dalam folder Google Drive bernama sesuai '
    'kode butir ini (konvensi penamaan dari dokumen "nama indikator_folder '
    'bukti"). Definisi butir, jenis input, dan target IKU masih perlu '
    'dilengkapi LP3M lewat halaman Kelola Instrumen.'
)


def seed(apps, schema_editor):
    Siklus = apps.get_model('ami_core', 'Siklus')
    Standar = apps.get_model('ami_core', 'Standar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    siklus = Siklus.objects.filter(is_current=True).first()
    if siklus is None:
        return

    for standar_kode, items in INDIKATOR_PER_STANDAR:
        try:
            standar = Standar.objects.get(kode=standar_kode)
        except Standar.DoesNotExist:
            continue
        for no_urut, (kode, judul) in enumerate(items, start=1):
            ButirPenilaian.objects.get_or_create(
                siklus=siklus, kode=kode,
                defaults=dict(
                    standar=standar, judul=judul, jenis_input='narasi',
                    bobot=1, is_wajib=True, is_kuantitatif=False,
                    panduan_pengisian=PANDUAN_DEFAULT, no_urut=no_urut,
                    is_aktif=True,
                ),
            )


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    all_kode = [kode for _, items in INDIKATOR_PER_STANDAR for kode, _ in items]
    ButirPenilaian.objects.filter(kode__in=all_kode).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0002_seed_reference_data'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
