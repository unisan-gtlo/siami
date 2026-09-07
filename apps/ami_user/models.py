from django.conf import settings
from django.db import models

from apps.ami_master.models import Fakultas, Prodi


class UserAmi(models.Model):
    """Ekstensi role & atribut AMI di atas Django auth.User.

    Desain asli (01_database/02_tables_master.sql) memisahkan profil dasar di
    schema `sso` dan meng-cache nama/email/foto di sini karena SSO adalah
    sistem terpisah. Karena SIAMI sekarang punya database sendiri yang
    terisolasi dan belum ada integrasi SSO nyata, extension ini langsung
    menempel ke auth.User bawaan Django (nama/email cukup diambil dari sana,
    tidak perlu di-cache ulang) -- field logical `sso_user_id` bisa
    ditambahkan lagi nanti begitu integrasi SSO benar-benar berjalan.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ami_profile',
    )
    nidn_nip = models.CharField(max_length=30, unique=True, null=True, blank=True)

    fakultas = models.ForeignKey(
        Fakultas, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_ami_set',
    )
    prodi = models.ForeignKey(
        Prodi, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_ami_set',
    )

    is_auditor_de = models.BooleanField(default=False)
    is_auditor_visitasi = models.BooleanField(default=False)
    is_upm = models.BooleanField(default=False)
    is_lp3m = models.BooleanField(default=False)
    is_pimpinan = models.BooleanField(default=False)

    sertifikasi_auditor = models.CharField(max_length=100, null=True, blank=True)
    pengalaman_audit_thn = models.PositiveIntegerField(null=True, blank=True)
    pakta_integritas_signed_at = models.DateTimeField(null=True, blank=True)
    pakta_integritas_file = models.CharField(max_length=500, null=True, blank=True)

    is_aktif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_ami'
        verbose_name = 'User AMI'
        verbose_name_plural = 'User AMI'
        ordering = ['user__username']

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Notifikasi(models.Model):
    """Notifikasi internal SI-AMI — in-app, email, WhatsApp."""

    TIPE_CHOICES = [
        ('info', 'Info'),
        ('reminder', 'Reminder'),
        ('tenggat', 'Tenggat'),
        ('eskalasi', 'Eskalasi'),
        ('persetujuan', 'Persetujuan'),
        ('penugasan_baru', 'Penugasan Baru'),
        ('sistem', 'Sistem'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    to_user = models.ForeignKey(UserAmi, on_delete=models.CASCADE, related_name='notifikasi_set')

    judul = models.CharField(max_length=300)
    isi = models.TextField(null=True, blank=True)
    tipe = models.CharField(max_length=30, choices=TIPE_CHOICES, null=True, blank=True)

    ref_entity = models.CharField(
        max_length=50, null=True, blank=True, help_text='"temuan", "fvtb", "penugasan_de", dll',
    )
    ref_entity_id = models.BigIntegerField(null=True, blank=True)
    ref_url = models.CharField(max_length=500, null=True, blank=True)

    channel_email = models.BooleanField(default=False)
    channel_wa = models.BooleanField(default=False)
    channel_inapp = models.BooleanField(default=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent_email = models.BooleanField(default=False)
    is_sent_wa = models.BooleanField(default=False)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifikasi'
        verbose_name = 'Notifikasi'
        verbose_name_plural = 'Notifikasi'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'is_read'], name='idx_notif_user_read'),
        ]

    def __str__(self):
        return self.judul
