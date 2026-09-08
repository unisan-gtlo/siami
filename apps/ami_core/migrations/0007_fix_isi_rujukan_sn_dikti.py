# Migrasi 0006 gagal mengisi rujukan_sn_dikti -- filter
# `rujukan_sn_dikti__in=['', None]` ternyata tidak menjangkau baris
# NULL (dikonfirmasi lewat query verifikasi: seluruh 58 butir riil
# masih null=True, filled=0 setelah 0006 diterapkan). Migrasi ini
# mengulang pengisian yang sama dengan Q(isnull=True) | Q(exact='')
# yang eksplisit dan tidak ambigu.
from django.db import migrations
from django.db.models import Q

# Duplikat dari 0006 -- modul migrasi berawalan angka tidak bisa
# di-import langsung sebagai identifier Python (`from .0006_x import y`
# adalah SyntaxError), jadi daftar rujukan disalin apa adanya di sini.
RUJUKAN_PER_STANDAR = {
    '1': (
        'Permendiktisaintek 39/2025 Pasal 64 (Standar Dikti tambahan oleh PT). '
        'Tidak ada pasal SN-Dikti spesifik untuk VMTS — basis utama Statuta/Renstra UNISAN.'
    ),
    '2': (
        'Permendiktisaintek 39/2025 Pasal 67-69 (SPMI). Tidak ada pasal SN-Dikti '
        'spesifik untuk tata pamong/tata kelola institusional.'
    ),
    '3': 'Permendiktisaintek 39/2025 Pasal 36-38 (penerimaan, penyiapan, layanan mahasiswa).',
    '4': 'Permendiktisaintek 39/2025 Pasal 46-47 (Standar Dosen dan Tenaga Kependidikan).',
    '5': 'Permendiktisaintek 39/2025 Pasal 48-50 (Sarana Prasarana) & Pasal 51 (Pembiayaan).',
    '6': 'Permendiktisaintek 39/2025 Pasal 44 (Kurikulum) & Pasal 11-25 (Proses Pembelajaran).',
    '7': 'Permendiktisaintek 39/2025 Pasal 52-57 (Standar Penelitian: luaran, proses, masukan).',
    '8': 'Permendiktisaintek 39/2025 Pasal 58-63 (Standar PkM: luaran, proses, masukan).',
}


def seed(apps, schema_editor):
    Standar = apps.get_model('ami_core', 'Standar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    for standar_kode, rujukan in RUJUKAN_PER_STANDAR.items():
        try:
            standar = Standar.objects.get(kode=standar_kode)
        except Standar.DoesNotExist:
            continue
        ButirPenilaian.objects.filter(
            Q(rujukan_sn_dikti__isnull=True) | Q(rujukan_sn_dikti=''),
            standar=standar,
        ).update(rujukan_sn_dikti=rujukan)


def unseed(apps, schema_editor):
    Standar = apps.get_model('ami_core', 'Standar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    for standar_kode, rujukan in RUJUKAN_PER_STANDAR.items():
        try:
            standar = Standar.objects.get(kode=standar_kode)
        except Standar.DoesNotExist:
            continue
        ButirPenilaian.objects.filter(standar=standar, rujukan_sn_dikti=rujukan).update(rujukan_sn_dikti=None)


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0006_isi_rujukan_sn_dikti_58_butir'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
