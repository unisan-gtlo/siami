from django.db import migrations

TAHAP = [
    dict(kode='AMI_ONLINE', nama='AMI Online (Self-Assessment)', no_urut=1,
         deskripsi='Auditee mengisi instrumen IKU-IKT secara mandiri di platform online',
         durasi_hari=30),
    dict(kode='DESK_EVAL', nama='Desk Evaluasi (DE)', no_urut=2,
         deskripsi='Auditor menelaah dokumen secara online dan memberikan skor binary 1/0',
         durasi_hari=21),
    dict(kode='VISITASI', nama='Visitasi Lapangan', no_urut=3,
         deskripsi='Auditor melakukan verifikasi langsung di prodi auditee',
         durasi_hari=14),
]

STANDAR = [
    dict(kode='1', nama='Visi, Misi, Tujuan, dan Strategi', nama_pendek='VMTS', no_urut=1, warna_hex='#0E5A8A'),
    dict(kode='2', nama='Tata Pamong, Tata Kelola, dan Kerjasama', nama_pendek='Tata Pamong', no_urut=2, warna_hex='#1B7BB8'),
    dict(kode='3', nama='Mahasiswa', nama_pendek='Mahasiswa', no_urut=3, warna_hex='#5BAEDB'),
    dict(kode='4', nama='Sumber Daya Manusia', nama_pendek='SDM', no_urut=4, warna_hex='#27AE60'),
    dict(kode='5', nama='Keuangan, Sarana, dan Prasarana', nama_pendek='Sapras', no_urut=5, warna_hex='#F2C94C'),
    dict(kode='6', nama='Pendidikan', nama_pendek='Pendidikan', no_urut=6, warna_hex='#E0A800'),
    dict(kode='7', nama='Penelitian', nama_pendek='Penelitian', no_urut=7, warna_hex='#E74C3C'),
    dict(kode='8', nama='Pengabdian Kepada Masyarakat', nama_pendek='PKM', no_urut=8, warna_hex='#9B59B6'),
    dict(kode='9', nama='Luaran dan Capaian Tridarma', nama_pendek='Luaran', no_urut=9, warna_hex='#2C3E50'),
]

SIKLUS = [
    dict(no_siklus=1, nama='Siklus 1', tahun_akademik='2018/2019', tgl_mulai='2018-04-01', tgl_selesai='2018-10-30', status='archived', is_current=False),
    dict(no_siklus=2, nama='Siklus 2', tahun_akademik='2019/2020', tgl_mulai='2019-04-01', tgl_selesai='2019-10-25', status='archived', is_current=False),
    dict(no_siklus=3, nama='Siklus 3', tahun_akademik='2020/2021', tgl_mulai='2020-04-01', tgl_selesai='2020-10-18', status='archived', is_current=False),
    dict(no_siklus=4, nama='Siklus 4', tahun_akademik='2021/2022', tgl_mulai='2021-04-01', tgl_selesai='2021-10-22', status='archived', is_current=False),
    dict(no_siklus=5, nama='Siklus 5', tahun_akademik='2022/2023', tgl_mulai='2022-04-01', tgl_selesai='2022-10-28', status='archived', is_current=False),
    dict(no_siklus=6, nama='Siklus 6', tahun_akademik='2023/2024', tgl_mulai='2023-04-01', tgl_selesai='2023-10-25', status='archived', is_current=False),
    dict(no_siklus=7, nama='Siklus 7', tahun_akademik='2024/2025', tgl_mulai='2024-04-01', tgl_selesai='2024-10-30', status='closed', is_current=False),
    dict(no_siklus=8, nama='Siklus 8', tahun_akademik='2025/2026', tgl_mulai='2026-05-01', tgl_selesai='2026-10-30', status='active', is_current=True),
]


def seed(apps, schema_editor):
    Tahap = apps.get_model('ami_core', 'Tahap')
    Standar = apps.get_model('ami_core', 'Standar')
    Siklus = apps.get_model('ami_core', 'Siklus')

    for row in TAHAP:
        Tahap.objects.get_or_create(kode=row['kode'], defaults=row)
    for row in STANDAR:
        Standar.objects.get_or_create(kode=row['kode'], defaults=row)
    for row in SIKLUS:
        Siklus.objects.get_or_create(no_siklus=row['no_siklus'], defaults=row)


def unseed(apps, schema_editor):
    apps.get_model('ami_core', 'Tahap').objects.filter(
        kode__in=[r['kode'] for r in TAHAP]).delete()
    apps.get_model('ami_core', 'Standar').objects.filter(
        kode__in=[r['kode'] for r in STANDAR]).delete()
    apps.get_model('ami_core', 'Siklus').objects.filter(
        no_siklus__in=[r['no_siklus'] for r in SIKLUS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
