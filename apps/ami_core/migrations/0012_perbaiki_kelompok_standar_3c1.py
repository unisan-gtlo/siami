# 0011 salah ketik: butir 3c.1 ("Kinerja akademik — kemampuan") diberi
# master_standar=STD-01 (Standar Kompetensi Lulusan, kelompok Luaran per
# MasterStandar/ref-enumerasi) tapi kelompok_standar ditulis 'P' (Proses)
# -- tidak konsisten dengan master_standar-nya sendiri, dan bertentangan
# dengan komentar kode 0011 yang justru menyebut "luaran mahasiswa".
# Diperbaiki jadi 'L' (Luaran) di sini.
from django.db import migrations


def seed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(kode='3c.1').update(kelompok_standar='L')


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(kode='3c.1').update(kelompok_standar='P')


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0011_lengkapi_domain_kelompok_master_standar_58_butir'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
