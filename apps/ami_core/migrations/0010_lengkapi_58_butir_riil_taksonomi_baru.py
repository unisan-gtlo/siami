# Melengkapi field taksonomi baru untuk 58 butir riil Siklus 8 (seed 0003):
# jenis_jawaban, sasaran_auditee, rubrik_skor generik, dan dasar_hukum
# (disalin dari rujukan_sn_dikti yang sudah diisi di 0007). domain,
# kelompok_standar, dan master_standar SENGAJA dibiarkan kosong -- pemetaan
# taksonomi Pasal 5 SN-Dikti yang presisi per butir belum bisa dipastikan
# tanpa peninjauan LP3M satu per satu (lihat MIGRASI-PERMEN-39-2025.md
# aturan #5 "jangan mengarang").
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

    butir_qs = ButirPenilaian.objects.filter(jenis_jawaban__isnull=True)
    for butir in butir_qs:
        butir.jenis_jawaban = 'JJ-1'
        butir.sasaran_auditee = ['AU-1']
        butir.rubrik_skor = RUBRIK_GENERIK
        if butir.rujukan_sn_dikti and not butir.dasar_hukum:
            butir.dasar_hukum = [butir.rujukan_sn_dikti]
        butir.save(update_fields=['jenis_jawaban', 'sasaran_auditee', 'rubrik_skor', 'dasar_hukum'])


def unseed(apps, schema_editor):
    ButirPenilaian = apps.get_model('ami_core', 'ButirPenilaian')
    ButirPenilaian.objects.filter(jenis_jawaban='JJ-1').update(
        jenis_jawaban=None, sasaran_auditee=None, rubrik_skor=None, dasar_hukum=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('ami_core', '0009_seed_ref_enumerasi_dan_master_standar'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
