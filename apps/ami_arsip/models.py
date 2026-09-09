from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models

from apps.ami_core.models import MasterStandar, Siklus
from apps.ami_master.models import Prodi
from apps.ami_user.models import UserAmi


class ArsipMetadata(models.Model):
    """Metadata arsip dokumen AMI lintas siklus + sync ke arsip.unisan-g.id."""

    KATEGORI_CHOICES = [
        ('form_penilaian', 'Form Penilaian'),
        ('temuan_ptk', 'Temuan PTK'),
        ('best_practice', 'Best Practice'),
        ('sk_rektor', 'SK Rektor'),
        ('notulen_rtm', 'Notulen RTM'),
        ('sertifikat_ami', 'Sertifikat AMI'),
        ('berita_acara', 'Berita Acara'),
        ('laporan_lengkap', 'Laporan Lengkap'),
        ('lainnya', 'Lainnya'),
    ]

    siklus = models.ForeignKey(
        Siklus, on_delete=models.SET_NULL, null=True, blank=True, related_name='arsip_set',
    )
    prodi = models.ForeignKey(
        Prodi, on_delete=models.SET_NULL, null=True, blank=True, related_name='arsip_set',
    )
    master_standar = models.ForeignKey(
        MasterStandar, on_delete=models.SET_NULL, null=True, blank=True, related_name='arsip_set',
        help_text='Standar SN-Dikti terkait dokumen ini, bila relevan.',
    )
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES)

    nama_dokumen = models.CharField(max_length=300)
    deskripsi = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='arsip/%Y/%m/')
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_mime_type = models.CharField(max_length=100, null=True, blank=True)
    file_hash_sha256 = models.CharField(max_length=64, null=True, blank=True)

    tags = ArrayField(models.CharField(max_length=50), null=True, blank=True)
    fulltext_content = models.TextField(
        null=True, blank=True, help_text='Konten hasil ekstraksi untuk fulltext search',
    )
    fulltext_search = SearchVectorField(null=True, blank=True, editable=False)

    synced_to_arsip = models.BooleanField(default=False)
    arsip_universitas_id = models.CharField(max_length=100, null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    retensi_sd_tahun = models.PositiveIntegerField(null=True, blank=True)
    is_permanen = models.BooleanField(default=False)

    is_publik = models.BooleanField(default=False)
    akses_role = ArrayField(models.CharField(max_length=50), null=True, blank=True)

    diunggah_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='arsip_diunggah_set',
    )
    diunggah_pada = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'arsip_metadata'
        verbose_name = 'Arsip'
        verbose_name_plural = 'Arsip'
        ordering = ['-diunggah_pada']
        indexes = [
            GinIndex(fields=['tags'], name='idx_arsip_tags_gin'),
            GinIndex(fields=['fulltext_search'], name='idx_arsip_fulltext_gin'),
        ]

    def __str__(self):
        return self.nama_dokumen

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Setara trigger fn_update_arsip_search() di desain SQL asli, dihitung
        # lewat query terpisah (bukan trigger DB) supaya bisa dites lewat ORM
        # biasa tanpa custom SQL yang belum bisa diverifikasi langsung.
        type(self).objects.filter(pk=self.pk).update(
            fulltext_search=SearchVector(
                'nama_dokumen', 'deskripsi', 'fulltext_content', config='indonesian',
            ),
        )


class PencarianArsipLog(models.Model):
    """Riwayat pencarian lintas siklus -- dicatat tiap kali ada pencarian
    teks (`q`) yang benar-benar dijalankan, bukan sekadar klik filter."""

    query = models.CharField(max_length=300)
    jumlah_hasil = models.PositiveIntegerField(default=0)
    siklus = models.ForeignKey(
        Siklus, on_delete=models.SET_NULL, null=True, blank=True, related_name='pencarian_arsip_set',
    )
    dicari_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='pencarian_arsip_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'arsip_pencarian_log'
        verbose_name = 'Riwayat Pencarian Arsip'
        verbose_name_plural = 'Riwayat Pencarian Arsip'
        ordering = ['-created_at']

    def __str__(self):
        return self.query
