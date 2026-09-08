# T2 (MIGRASI-PERMEN-39-2025.md): petakan status_akreditasi awal untuk 16
# prodi riil dari akreditasi_peringkat yang sudah ada (bukan enum lama yang
# "dimigrasikan" -- field status_akreditasi memang baru dibuat di sini,
# tidak ada nilai lama yang perlu dipertahankan sebagai legacy karena
# belum pernah ada field seperti ini sebelumnya).
#
# Data riil terverifikasi (query produksi, 8 Sep 2026): seluruh 16 prodi
# punya akreditasi_peringkat terisi (B: 5, Baik: 8, Baik Sekali: 3) --
# TIDAK ADA yang 'Belum'/'Unggul'/'A'/'C'/'Terakreditasi'. Karena semuanya
# sudah punya peringkat resmi (bukan prodi baru/belum diakreditasi),
# semuanya dipetakan ke status_akreditasi='terakreditasi' -- status yang
# memenuhi syarat Pasal 70 ayat (4), sehingga TIDAK ADA prodi yang
# tiba-tiba "terblokir" oleh field baru ini (kriteria penerimaan T2/T4).
# status_asal menyimpan peringkat asli untuk jejak audit.
from django.db import migrations


def seed(apps, schema_editor):
    Prodi = apps.get_model('ami_master', 'Prodi')
    qs = Prodi.objects.filter(
        status_akreditasi__isnull=True, akreditasi_peringkat__isnull=False,
    ).exclude(akreditasi_peringkat='Belum')
    for prodi in qs:
        prodi.status_asal = prodi.akreditasi_peringkat
        prodi.status_akreditasi = 'terakreditasi'
        prodi.save(update_fields=['status_akreditasi', 'status_asal'])

    # Prodi berperingkat 'Belum' (bila ada) dipetakan eksplisit ke
    # tidak_terakreditasi, bukan dibiarkan kosong.
    Prodi.objects.filter(
        status_akreditasi__isnull=True, akreditasi_peringkat='Belum',
    ).update(status_akreditasi='tidak_terakreditasi', status_asal='Belum')


def unseed(apps, schema_editor):
    Prodi = apps.get_model('ami_master', 'Prodi')
    Prodi.objects.filter(status_asal__isnull=False).update(status_akreditasi=None, status_asal=None)


class Migration(migrations.Migration):

    dependencies = [
        ('ami_master', '0005_prodi_status_akreditasi_prodi_status_asal'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
