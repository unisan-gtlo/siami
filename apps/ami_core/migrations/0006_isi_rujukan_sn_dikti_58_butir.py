# Mengisi ButirPenilaian.rujukan_sn_dikti untuk 58 indikator riil (seed
# 0003) -- field ini KOSONG untuk semua 58 baris sejak awal (lihat 0003),
# jadi ini pengisian pertama, bukan penggantian sitasi lama.
#
# Sitasi mengacu Permendiktisaintek 39/2025. Standar 1 (VMTS) dan Standar 2
# (Tata Pamong/Tata Kelola) TIDAK punya padanan pasal SN-Dikti yang presisi
# -- keduanya kriteria institusional/BAN-PT, bukan topik yang diatur pasal
# per pasal di 39/2025. Untuk keduanya dicantumkan pasal payung terdekat
# (Pasal 64 dan Pasal 67-69) dengan catatan eksplisit "tidak ada pasal
# spesifik", BUKAN sitasi presisi yang dikarang -- lihat larangan
# "jangan mengarang isi pasal" di MIGRASI-PERMEN-39-2025.md bagian 3.5.
# Standar 3 s.d. 8 punya padanan pasal SN-Dikti yang jelas (kemahasiswaan,
# SDM, sarpras/pembiayaan, kurikulum/pembelajaran, penelitian, PkM).
from django.db import migrations

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
            standar=standar, rujukan_sn_dikti__in=['', None],
        ).update(rujukan_sn_dikti=rujukan)


def unseed(apps, schema_editor):
    Standar = apps.get_model('ami_core', 'Standar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    for standar_kode, rujukan in RUJUKAN_PER_STANDAR.items():
        try:
            standar = Standar.objects.get(kode=standar_kode)
        except Standar.DoesNotExist:
            continue
        ButirPenilaian.objects.filter(standar=standar, rujukan_sn_dikti=rujukan).update(rujukan_sn_dikti='')


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0005_seed_regulasi_acuan'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
