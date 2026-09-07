# Data diambil read-only dari unisan_db.master (schema SIMDA) di server
# unisan-g, dicek manual lewat psql pada 2026-09-07 -- bukan hasil sync API
# otomatis (belum ada). source_schema/source_id disimpan supaya sync
# terjadwal beneran nanti tinggal menimpa baris yang sama.
from django.db import migrations

FAKULTAS = [
    dict(kode='FE', nama='Fakultas Ekonomi', nama_singkat='Fak. Ekonomi', urutan=1),
    dict(kode='FH', nama='Fakultas Hukum', nama_singkat='Fak. Hukum', urutan=2),
    dict(kode='FS', nama='Fakultas Ilmu Sosial dan Ilmu Politik', nama_singkat='FS', urutan=3),
    dict(kode='FK', nama='Fakultas Ilmu Komputer', nama_singkat='FIKOM', urutan=4),
    dict(kode='FP', nama='Fakultas Pertanian', nama_singkat='Fak. Pertanian', urutan=5),
    dict(kode='FT', nama='Fakultas Teknik', nama_singkat='Fak. Teknik', urutan=6),
    dict(kode='PPS', nama='Program Pascasarjana', nama_singkat='Pascasarjana', urutan=7),
]

# (kode_prodi, kode_pddikti, nama, jenjang, akreditasi_peringkat, no_sk_akreditasi,
#  tgl_sk_akreditasi, berlaku_sampai_akreditasi, no_sk_pendirian, kode_fakultas)
PRODI = [
    ('E11', '62201', 'Akuntansi', 'S1', 'B', '', None, None, '', 'FE'),
    ('E21', '61201', 'Manajemen', 'S1', 'B', '', None, None, '', 'FE'),
    ('ES2', '61101', 'Manajemen', 'S2', 'Baik', '', None, None, '', 'PPS'),
    ('H11', '74201', 'Ilmu Hukum', 'S1', 'B', '', None, None, '', 'FH'),
    ('HS2', '74101', 'Ilmu Hukum', 'S2', 'Baik Sekali', '', None, None, '', 'PPS'),
    ('K11', '57201', 'Sistem Informasi', 'S1', 'Baik', '', None, None, '', 'FK'),
    ('P21', '54211', 'Agroteknologi', 'S1', 'Baik', '', None, None, '', 'FP'),
    ('P22', '54201', 'Agribisnis', 'S1', 'Baik Sekali', '', None, None, '', 'FP'),
    ('P23', '41231', 'Teknologi Hasil Pertanian', 'S1', 'B', '', None, None, '', 'FP'),
    ('S21', '65201', 'Ilmu Pemerintahan', 'S1', 'B', '', None, None, '', 'FS'),
    ('S22', '70201', 'Ilmu Komunikasi', 'S1', 'Baik', '', None, None, '', 'FS'),
    ('SS2', '65101', 'Ilmu Pemerintahan', 'S2', 'Baik', '', None, None, '', 'PPS'),
    ('T11', '23201', 'Teknik Arsitektur', 'S1', 'Baik', '', None, None, '', 'FT'),
    ('T21', '20201', 'Teknik Elektro', 'S1', 'Baik Sekali', '', None, None, '', 'FT'),
    ('T31', '55201', 'Teknik Informatika', 'S1', 'Baik',
     '13204/SK/BAN-PT/Akred-PMT/S/XII/2021', '2021-12-15', '2026-12-15', '84/D/O/2001', 'FK'),
    ('T41', '90241', 'Desain Komunikasi Visual', 'S1', 'Baik', '', None, None, '', 'FK'),
]


def seed(apps, schema_editor):
    Fakultas = apps.get_model('ami_master', 'Fakultas')
    Prodi = apps.get_model('ami_master', 'Prodi')

    fakultas_by_kode = {}
    for row in FAKULTAS:
        obj, _ = Fakultas.objects.update_or_create(
            kode=row['kode'],
            defaults=dict(
                nama=row['nama'], nama_singkat=row['nama_singkat'],
                source_schema='master', source_id=row['kode'],
            ),
        )
        fakultas_by_kode[row['kode']] = obj

    for (kode, kode_pddikti, nama, jenjang, peringkat, no_sk_akred,
         tgl_sk_akred, berlaku_sd, no_sk_pendirian, kode_fakultas) in PRODI:
        Prodi.objects.update_or_create(
            kode=kode,
            defaults=dict(
                fakultas=fakultas_by_kode[kode_fakultas],
                kode_pddikti=kode_pddikti,
                nama=nama,
                strata=jenjang,
                akreditasi_peringkat=peringkat or None,
                akreditasi_no_sk=no_sk_akred or None,
                akreditasi_tgl_sk=tgl_sk_akred,
                akreditasi_berlaku_sd=berlaku_sd,
                sk_pendirian_no=no_sk_pendirian or None,
                source_schema='master', source_id=kode,
            ),
        )


def unseed(apps, schema_editor):
    apps.get_model('ami_master', 'Prodi').objects.filter(
        kode__in=[p[0] for p in PRODI]).delete()
    apps.get_model('ami_master', 'Fakultas').objects.filter(
        kode__in=[f['kode'] for f in FAKULTAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_master', '0002_alter_fakultas_source_id_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
