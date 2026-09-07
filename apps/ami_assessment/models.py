from django.contrib.postgres.indexes import GinIndex
from django.db import models

from apps.ami_core.models import ButirPenilaian, Siklus
from apps.ami_master.models import Prodi
from apps.ami_user.models import UserAmi


class Pengisian(models.Model):
    """Header self-assessment AMI per prodi per siklus."""

    STATUS_CHOICES = [
        ('belum_mulai', 'Belum Mulai'),
        ('sedang_diisi', 'Sedang Diisi'),
        ('submit', 'Submit'),
        ('validasi_upm', 'Validasi UPM'),
        ('siap_de', 'Siap DE'),
        ('completed', 'Completed'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='pengisian_set')
    prodi = models.ForeignKey(Prodi, on_delete=models.PROTECT, related_name='pengisian_set')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='belum_mulai')

    total_butir = models.PositiveIntegerField(default=0)
    butir_terisi = models.PositiveIntegerField(default=0)

    skor_total = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    skor_per_standar = models.JSONField(null=True, blank=True)

    operator = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pengisian_operator_set',
    )
    upm_validator = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pengisian_validator_set',
    )

    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    catatan = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pengisian'
        verbose_name_plural = 'Pengisian'
        ordering = ['-siklus', 'prodi']
        constraints = [
            models.UniqueConstraint(fields=['siklus', 'prodi'], name='uniq_pengisian_siklus_prodi'),
        ]

    def __str__(self):
        return f'{self.prodi} — {self.siklus}'

    @property
    def persentase_progress(self):
        """Setara kolom generated di 02_tables_master.sql (dihitung di Python,
        bukan generated column DB, supaya tidak perlu ekspresi SQL kustom
        yang belum bisa diverifikasi tanpa akses langsung ke Postgres)."""
        if not self.total_butir:
            return 0
        return round(self.butir_terisi / self.total_butir * 100, 2)


class JawabanButir(models.Model):
    """Detail jawaban auditee untuk setiap butir penilaian."""

    SUMBER_DATA_CHOICES = [
        ('manual', 'Manual'),
        ('auto_pmb', 'Auto PMB'),
        ('auto_sikd', 'Auto SIKD'),
        ('auto_akademik', 'Auto Akademik'),
        ('import_excel', 'Import Excel'),
    ]

    pengisian = models.ForeignKey(Pengisian, on_delete=models.CASCADE, related_name='jawaban_set')
    butir = models.ForeignKey(ButirPenilaian, on_delete=models.PROTECT, related_name='jawaban_set')

    nilai_kuantitatif = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    nilai_pilihan = models.CharField(max_length=200, null=True, blank=True)
    nilai_narasi = models.TextField(null=True, blank=True)
    nilai_tabel = models.JSONField(null=True, blank=True)
    nilai_auto = models.JSONField(null=True, blank=True)

    rasio_hasil = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    persentase_capaian = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    memenuhi_iku = models.BooleanField(null=True, blank=True)

    sumber_data = models.CharField(max_length=30, choices=SUMBER_DATA_CHOICES, default='manual')

    catatan_auditee = models.TextField(null=True, blank=True)

    is_terisi = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    diisi_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='jawaban_set',
    )
    diisi_pada = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jawaban_butir'
        verbose_name_plural = 'Jawaban Butir'
        constraints = [
            models.UniqueConstraint(fields=['pengisian', 'butir'], name='uniq_jawaban_pengisian_butir'),
        ]
        indexes = [
            GinIndex(fields=['nilai_tabel'], name='idx_jawaban_nilai_tabel_gin'),
        ]

    def __str__(self):
        return f'{self.pengisian} — {self.butir.kode}'


class DokumenBukti(models.Model):
    """Repository dokumen bukti pendukung AMI — file upload, link, atau cross-schema."""

    JENIS_SUMBER_CHOICES = [
        ('upload_file', 'Upload File'),
        ('link_drive', 'Link Drive'),
        ('link_url', 'Link URL'),
        ('auto_api', 'Auto API'),
        ('cross_schema', 'Cross Schema'),
    ]
    STATUS_CHOICES = [
        ('belum_diverifikasi', 'Belum Diverifikasi'),
        ('menunggu_upm', 'Menunggu UPM'),
        ('terverifikasi', 'Terverifikasi'),
        ('ditolak', 'Ditolak'),
        ('perlu_revisi', 'Perlu Revisi'),
    ]

    pengisian = models.ForeignKey(Pengisian, on_delete=models.CASCADE, related_name='dokumen_set')
    butir = models.ForeignKey(
        ButirPenilaian, on_delete=models.SET_NULL, null=True, blank=True, related_name='dokumen_set',
    )
    jawaban = models.ForeignKey(
        JawabanButir, on_delete=models.SET_NULL, null=True, blank=True, related_name='dokumen_set',
    )

    nama_dokumen = models.CharField(max_length=300)
    deskripsi = models.TextField(null=True, blank=True)

    jenis_sumber = models.CharField(max_length=20, choices=JENIS_SUMBER_CHOICES)

    # Setara kolom `file_path` di desain asli, tapi pakai FileField supaya
    # Django yang mengelola penyimpanan fisik di MEDIA_ROOT.
    file = models.FileField(upload_to='dokumen_bukti/%Y/%m/', null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_mime_type = models.CharField(max_length=100, null=True, blank=True)

    link_url = models.URLField(max_length=1000, null=True, blank=True)
    link_terverifikasi = models.BooleanField(default=False)
    link_last_checked = models.DateTimeField(null=True, blank=True)

    api_endpoint = models.CharField(max_length=500, null=True, blank=True)
    cross_schema_ref = models.JSONField(null=True, blank=True)

    format = models.CharField(max_length=20, null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='belum_diverifikasi')
    catatan_verifikasi = models.TextField(null=True, blank=True)
    diverifikasi_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='dokumen_diverifikasi_set',
    )
    diverifikasi_pada = models.DateTimeField(null=True, blank=True)

    diunggah_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='dokumen_diunggah_set',
    )
    diunggah_pada = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dokumen_bukti'
        verbose_name_plural = 'Dokumen Bukti'

    def __str__(self):
        return self.nama_dokumen
