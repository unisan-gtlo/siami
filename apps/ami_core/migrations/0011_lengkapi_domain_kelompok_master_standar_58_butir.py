# Melengkapi domain/kelompok_standar/master_standar untuk 58 butir riil
# Siklus 8, atas permintaan eksplisit pengguna (sebelumnya sengaja
# dikosongkan di 0010 karena butuh peninjauan per-butir, bukan tebakan
# per-Standar). Pemetaan di bawah didasarkan pada JUDUL tiap butir
# (dari seed 0003), bukan dokumen hukum yang diverifikasi terpisah --
# LP3M tetap perlu meninjau/menyesuaikan lewat Kelola Instrumen bila ada
# yang keliru, terutama untuk Standar 7 & 8 (Penelitian/PKM) yang
# mencampur topik luaran dan proses dalam satu Standar lama.
#
# BASE = default per Standar lama; OVERRIDE = pengecualian per kode
# karena judul butirnya jelas condong ke kelompok lain daripada
# default Standar-nya (mis. "kegiatan dan hasilnya" -> Luaran,
# bukan Proses seperti butir Penelitian/PKM lainnya).
from django.db import migrations

BASE = {
    # standar_kode: (domain, kelompok_standar, master_standar_kode)
    '1': ('NAK', 'T', 'STD-15'),  # VMTS -> Standar Dikti yang Ditetapkan PT
    '2': ('NAK', 'T', 'STD-16'),  # Tata Pamong/Tata Kelola -> SPMI
    '3': ('PDD', 'P', 'STD-04'),  # Mahasiswa -> Pengelolaan (Pasal 31-39, termasuk 36-38)
    '4': ('PDD', 'M', 'STD-06'),  # SDM -> Dosen & Tenaga Kependidikan
    '5': ('PDD', 'M', 'STD-07'),  # Keuangan & Sarpras -> default Sarpras
    '6': ('PDD', 'P', 'STD-03'),  # Kurikulum & Pembelajaran -> default Jaminan Pembelajaran/Penilaian
    '7': ('PNL', 'P', 'STD-10'),  # Penelitian -> default Proses Penelitian
    '8': ('PKM', 'P', 'STD-13'),  # PKM -> default Proses PkM
}

OVERRIDE = {
    '3c.1': ('P', 'STD-01'),   # "Kinerja akademik — kemampuan" -> capaian/luaran mahasiswa, bukan proses pengelolaan
    '5a.1': ('M', 'STD-08'),   # "Keuangan — 4 Pilar" -> Pembiayaan, bukan Sarpras
    '5a.2': ('M', 'STD-08'),   # "Keuangan — usaha keberlanjutan" -> Pembiayaan
    '6a.1': ('M', 'STD-05'),   # "Kurikulum — peta, CPL" -> Standar Isi (Pasal 44)
    '6a.2': ('M', 'STD-05'),
    '6a.3': ('M', 'STD-05'),
    '6a.4': ('M', 'STD-05'),
    '7a.2': ('L', 'STD-09'),   # "Penelitian — kegiatan dan hasilnya" -> condong Luaran
    '7b.2': ('L', 'STD-12'),   # "PKM — kegiatan dan hasilnya/kontribusi" -> condong Luaran
}


def seed(apps, schema_editor):
    Standar = apps.get_model('ami_core', 'Standar')
    MasterStandar = apps.get_model('ami_core', 'MasterStandar')
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')

    for standar_kode, (domain, kelompok, ms_kode) in BASE.items():
        standar = Standar.objects.filter(kode=standar_kode).first()
        if not standar:
            continue
        master_standar = MasterStandar.objects.filter(kode=ms_kode).first()
        ButirPenilaian.objects.filter(standar=standar, domain__isnull=True).update(
            domain=domain, kelompok_standar=kelompok, master_standar=master_standar,
        )

    for kode, (kelompok, ms_kode) in OVERRIDE.items():
        master_standar = MasterStandar.objects.filter(kode=ms_kode).first()
        ButirPenilaian.objects.filter(kode=kode).update(
            kelompok_standar=kelompok, master_standar=master_standar,
        )


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(kode__in=list(OVERRIDE.keys())).update(
        domain=None, kelompok_standar=None, master_standar=None,
    )
    for standar_kode in BASE:
        ButirPenilaian.objects.filter(standar__kode=standar_kode).exclude(
            kode__in=list(OVERRIDE.keys()),
        ).update(domain=None, kelompok_standar=None, master_standar=None)


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0010_lengkapi_58_butir_riil_taksonomi_baru'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
