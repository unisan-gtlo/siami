# Menyelesaikan temuan kandidat duplikat T8: seluruh 58 butir lama
# (kode format "1a.1" dst, taksonomi institusional) tumpang tindih
# substansinya dengan 98 butir baru (kode "AMI8.*", taksonomi Pasal 5
# SN-Dikti). Atas keputusan eksplisit pengguna (bukan asumsi agen):
# 58 butir lama dinonaktifkan untuk Siklus 8, penilaian selanjutnya
# memakai 98 butir baru saja.
#
# Ini SOFT DELETE (status='nonaktif'), bukan penghapusan -- sesuai
# larangan eksplisit MIGRASI-PERMEN-39-2025.md prinsip #1: "Jangan
# menghapus butir instrumen yang sudah memiliki data penilaian."
# 7 JawabanButir riil (self-assessment prodi S21) yang terikat ke
# butir-butir ini TETAP UTUH di database -- hanya tidak lagi tampil di
# daftar butir aktif untuk pengisian baru. LP3M akan menginformasikan
# manual ke S21 bahwa instrumen berganti versi dan self-assessment perlu
# diisi ulang dengan 98 butir baru.
from django.db import migrations


def seed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(
        kode__regex=r'^[0-9]', status='aktif',
    ).update(status='nonaktif', is_aktif=False)


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(
        kode__regex=r'^[0-9]', status='nonaktif',
    ).update(status='aktif', is_aktif=True)


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0013_impor_98_butir_master_siklus8'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
