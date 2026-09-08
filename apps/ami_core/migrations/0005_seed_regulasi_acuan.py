# Seed RegulasiAcuan: Permendikbudristek 53/2023 (dicabut) dan
# Permendiktisaintek 39/2025 (berlaku, mencabut 53/2023 -- Pasal 117).
# Siklus 8 (is_current) dan siklus setelahnya diasumsikan berjalan di
# bawah 39/2025 (diundangkan 2 Sep 2025); siklus 1-7 di bawah 53/2023,
# yang menjadi acuan sepanjang masa berjalannya siklus tersebut.
from django.db import migrations


def seed(apps, schema_editor):
    RegulasiAcuan = apps.get_model('ami_core', 'RegulasiAcuan')
    Siklus = apps.get_model('ami_core', 'Siklus')

    permen_53, _ = RegulasiAcuan.objects.get_or_create(
        kode='PERMEN_53_2023',
        defaults=dict(
            nama_lengkap=(
                'Peraturan Menteri Pendidikan, Kebudayaan, Riset, dan Teknologi '
                'Republik Indonesia Nomor 53 Tahun 2023 tentang Penjaminan Mutu '
                'Pendidikan Tinggi'
            ),
            nama_pendek='Permendikbudristek 53/2023',
            berita_negara='Berita Negara RI Tahun 2023 Nomor 638',
            status='dicabut',
        ),
    )

    permen_39, _ = RegulasiAcuan.objects.get_or_create(
        kode='PERMEN_39_2025',
        defaults=dict(
            nama_lengkap=(
                'Peraturan Menteri Pendidikan Tinggi, Sains, dan Teknologi '
                'Republik Indonesia Nomor 39 Tahun 2025 tentang Penjaminan Mutu '
                'Pendidikan Tinggi'
            ),
            nama_pendek='Permendiktisaintek 39/2025',
            berita_negara='Berita Negara RI Tahun 2025 Nomor 661',
            tanggal_tetap='2025-08-28',
            tanggal_undang='2025-09-02',
            mencabut=permen_53,
            status='berlaku',
        ),
    )

    Siklus.objects.filter(is_current=True).update(regulasi_acuan=permen_39)
    Siklus.objects.exclude(is_current=True).filter(regulasi_acuan__isnull=True).update(regulasi_acuan=permen_53)


def unseed(apps, schema_editor):
    Siklus = apps.get_model('ami_core', 'Siklus')
    RegulasiAcuan = apps.get_model('ami_core', 'RegulasiAcuan')
    Siklus.objects.update(regulasi_acuan=None)
    RegulasiAcuan.objects.filter(kode__in=['PERMEN_53_2023', 'PERMEN_39_2025']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0004_regulasiacuan_siklus_regulasi_acuan'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
