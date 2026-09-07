from django.db import models

from apps.ami_assessment.models import Pengisian
from apps.ami_core.models import ButirPenilaian, Siklus
from apps.ami_de.models import DePenilaian
from apps.ami_user.models import UserAmi
from apps.ami_visitasi.models import Visitasi

KLASIFIKASI_CHOICES = [
    ('KTB', 'Ketidaksesuaian Berat'),
    ('KTS', 'Ketidaksesuaian Sedang'),
    ('OB', 'Observasi'),
    ('BP', 'Best Practice'),
]


class Temuan(models.Model):
    """Temuan AMI — konsolidasi dari DE dan Visitasi, klasifikasi KTB/KTS/OB/BP."""

    SUMBER_CHOICES = [
        ('de', 'Desk Evaluasi'),
        ('visitasi', 'Visitasi'),
        ('manual', 'Manual'),
    ]
    URGENSI_CHOICES = [
        ('rendah', 'Rendah'),
        ('sedang', 'Sedang'),
        ('tinggi', 'Tinggi'),
        ('kritis', 'Kritis'),
    ]
    STATUS_CHOICES = [
        ('baru', 'Baru'),
        ('diidentifikasi', 'Diidentifikasi'),
        ('rencana_tindak_lanjut', 'Rencana Tindak Lanjut'),
        ('sedang_tindak_lanjut', 'Sedang Tindak Lanjut'),
        ('verifikasi', 'Verifikasi'),
        ('closed', 'Closed'),
        ('eskalasi', 'Eskalasi'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='temuan_set')
    pengisian = models.ForeignKey(Pengisian, on_delete=models.PROTECT, related_name='temuan_set')
    butir = models.ForeignKey(
        ButirPenilaian, on_delete=models.SET_NULL, null=True, blank=True, related_name='temuan_set',
    )

    sumber_temuan = models.CharField(max_length=20, choices=SUMBER_CHOICES)
    de_penilaian = models.ForeignKey(
        DePenilaian, on_delete=models.SET_NULL, null=True, blank=True, related_name='temuan_set',
    )
    visitasi = models.ForeignKey(
        Visitasi, on_delete=models.SET_NULL, null=True, blank=True, related_name='temuan_set',
    )

    klasifikasi = models.CharField(max_length=10, choices=KLASIFIKASI_CHOICES)
    no_temuan = models.CharField(max_length=50, null=True, blank=True, help_text='Auto: "T-S8-001"')

    judul = models.CharField(max_length=300)
    deskripsi_problem = models.TextField()
    lokasi_temuan = models.CharField(max_length=300, null=True, blank=True)
    standar_dilanggar = models.CharField(max_length=500, null=True, blank=True)
    bukti_referensi = models.TextField(null=True, blank=True)

    dampak = models.TextField(null=True, blank=True)
    urgensi = models.CharField(max_length=10, choices=URGENSI_CHOICES, null=True, blank=True)

    tenggat_tindak_lanjut = models.DateField(
        null=True, blank=True, help_text='KTB: 30 hari, KTS: 60 hari, OB: 90 hari',
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='baru')

    layak_replikasi = models.BooleanField(default=False)
    knowledge_base_id = models.IntegerField(null=True, blank=True)

    dilaporkan_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='temuan_dilaporkan_set',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'temuan'
        verbose_name_plural = 'Temuan'
        ordering = ['-siklus', 'klasifikasi']

    def __str__(self):
        return self.no_temuan or self.judul


class Fvtb(models.Model):
    """Form Verifikasi Tindak Lanjut — tracking PDCA per temuan."""

    STATUS_CHOICES = [
        ('plan', 'Plan'),
        ('do', 'Do'),
        ('check', 'Check'),
        ('act', 'Act'),
        ('closed', 'Closed'),
        ('eskalasi', 'Eskalasi'),
    ]

    temuan = models.ForeignKey(Temuan, on_delete=models.PROTECT, related_name='fvtb_set')
    no_fvtb = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # PLAN
    rencana_tindakan = models.TextField()
    pic = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='fvtb_pic_set',
    )
    pic_unit = models.CharField(max_length=200, null=True, blank=True)
    target_capaian = models.TextField(null=True, blank=True)
    estimasi_anggaran = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sumber_anggaran = models.CharField(max_length=200, null=True, blank=True)

    # DO
    progress_persen = models.PositiveSmallIntegerField(default=0)
    update_terakhir = models.TextField(null=True, blank=True)
    update_pada = models.DateTimeField(null=True, blank=True)

    tgl_mulai = models.DateField(null=True, blank=True)
    tenggat_selesai = models.DateField()
    tgl_selesai_aktual = models.DateField(null=True, blank=True)

    # CHECK
    sudah_diverifikasi = models.BooleanField(default=False)
    verifikator = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='fvtb_verifikator_set',
    )
    catatan_verifikasi = models.TextField(null=True, blank=True)
    bukti_verifikasi = models.JSONField(null=True, blank=True, help_text='Array id DokumenBukti')
    diverifikasi_pada = models.DateTimeField(null=True, blank=True)

    # ACT
    standarisasi_dilakukan = models.BooleanField(default=False)
    catatan_standarisasi = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan')

    last_notifikasi_sent = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fvtb'
        verbose_name = 'FVTB'
        verbose_name_plural = 'FVTB'
        ordering = ['-tenggat_selesai']
        constraints = [
            models.CheckConstraint(
                check=models.Q(progress_persen__gte=0) & models.Q(progress_persen__lte=100),
                name='chk_fvtb_progress_0_100',
            ),
        ]

    def __str__(self):
        return self.no_fvtb or f'FVTB — {self.temuan}'


class FvtbProgressLog(models.Model):
    """Log perubahan progress F-VTB untuk traceability tindak lanjut."""

    fvtb = models.ForeignKey(Fvtb, on_delete=models.CASCADE, related_name='progress_log_set')

    progress_sebelum = models.PositiveSmallIntegerField(null=True, blank=True)
    progress_sesudah = models.PositiveSmallIntegerField(null=True, blank=True)
    update_text = models.TextField()
    bukti_url = models.CharField(max_length=500, null=True, blank=True)

    diupdate_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='fvtb_log_set',
    )
    diupdate_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fvtb_progress_log'
        verbose_name = 'Log Progress FVTB'
        verbose_name_plural = 'Log Progress FVTB'
        ordering = ['-diupdate_pada']

    def __str__(self):
        return f'{self.fvtb} — {self.progress_sebelum}% → {self.progress_sesudah}%'
