# CSV master_butir_ami_siklus8_2026.csv tidak punya kolom Rubrik Skor, jadi
# migrasi impor 0013 tidak mengisi `rubrik_skor` sama sekali untuk 98 butir
# baru -- ditemukan lewat pertanyaan pengguna soal bagaimana skor bekerja
# untuk contoh butir riil (AMI8.PDD.P.32 punya jenis_jawaban='JJ-1' tapi
# rubrik_skor=None, artinya kotak "Rubrik Penilaian" di form DE tidak akan
# muncul untuk auditor). Migrasi 0010 sudah mengisi rubrik generik yang sama
# untuk 58 butir lama -- disalin apa adanya di sini untuk seluruh butir baru
# berjenis Skala 0-4 (JJ-1) yang belum punya rubrik.
from django.db import migrations

RUBRIK_GENERIK = [
    {'skor': 4, 'sebutan': 'Sangat Baik / Melampaui', 'deskripsi': (
        'Standar terpenuhi seluruhnya, terdokumentasi lengkap, konsisten '
        'dilaksanakan minimal 2 siklus, dan terdapat bukti peningkatan atau '
        'praktik baik yang dapat direplikasi.'
    )},
    {'skor': 3, 'sebutan': 'Baik / Terpenuhi', 'deskripsi': (
        'Standar terpenuhi dan terdokumentasi, namun pelaksanaan belum '
        'sepenuhnya konsisten atau bukti belum lengkap pada sebagian aspek.'
    )},
    {'skor': 2, 'sebutan': 'Cukup', 'deskripsi': (
        'Standar terpenuhi sebagian. Terdapat dokumen/kebijakan, tetapi '
        'implementasi belum berjalan atau tidak dapat dibuktikan.'
    )},
    {'skor': 1, 'sebutan': 'Kurang', 'deskripsi': (
        'Standar belum terpenuhi. Hanya terdapat rencana atau dokumen '
        'parsial tanpa bukti pelaksanaan.'
    )},
    {'skor': 0, 'sebutan': 'Tidak Ada', 'deskripsi': (
        'Tidak terdapat kebijakan, dokumen, maupun bukti pelaksanaan sama sekali.'
    )},
]


def seed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(
        jenis_jawaban='JJ-1', rubrik_skor__isnull=True,
    ).update(rubrik_skor=RUBRIK_GENERIK)


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(
        kode__startswith='AMI', jenis_jawaban='JJ-1', rubrik_skor=RUBRIK_GENERIK,
    ).update(rubrik_skor=None)


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0014_nonaktifkan_58_butir_lama'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
