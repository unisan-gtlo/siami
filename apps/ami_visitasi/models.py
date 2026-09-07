from django.db import models

from apps.ami_assessment.models import Pengisian
from apps.ami_core.models import Siklus
from apps.ami_user.models import UserAmi


class Visitasi(models.Model):
    """Header pelaksanaan visitasi lapangan per prodi."""

    KONFIRMASI_CHOICES = [
        ('belum_konfirmasi', 'Belum Konfirmasi'),
        ('dikonfirmasi', 'Dikonfirmasi'),
        ('minta_reschedule', 'Minta Reschedule'),
        ('ditolak', 'Ditolak'),
    ]
    STATUS_CHOICES = [
        ('terjadwal', 'Terjadwal'),
        ('dimulai', 'Dimulai'),
        ('on_progress', 'On Progress'),
        ('selesai', 'Selesai'),
        ('closing_done', 'Closing Done'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='visitasi_set')
    pengisian = models.ForeignKey(Pengisian, on_delete=models.PROTECT, related_name='visitasi_set')

    tgl_visitasi = models.DateField()
    waktu_mulai = models.TimeField(null=True, blank=True)
    waktu_selesai = models.TimeField(null=True, blank=True)
    tempat = models.CharField(max_length=300, null=True, blank=True)

    ketua_tim = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='visitasi_ketua_set',
    )
    notulis = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='visitasi_notulis_set',
    )

    sk_no = models.CharField(max_length=100, null=True, blank=True)
    sk_tgl = models.DateField(null=True, blank=True)
    sk_file = models.CharField(max_length=500, null=True, blank=True)

    konfirmasi_status = models.CharField(
        max_length=20, choices=KONFIRMASI_CHOICES, default='belum_konfirmasi',
    )
    konfirmasi_pada = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='terjadwal')

    ba_opening_file = models.CharField(max_length=500, null=True, blank=True)
    ba_closing_file = models.CharField(max_length=500, null=True, blank=True)
    sertifikat_file = models.CharField(max_length=500, null=True, blank=True)

    tgl_closing = models.DateField(null=True, blank=True)
    catatan_closing = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visitasi'
        verbose_name_plural = 'Visitasi'
        ordering = ['-tgl_visitasi']
        constraints = [
            models.UniqueConstraint(
                fields=['siklus', 'pengisian'], name='uniq_visitasi_siklus_pengisian',
            ),
        ]

    def __str__(self):
        return f'Visitasi {self.pengisian.prodi} — {self.tgl_visitasi}'


class VisitasiAnggota(models.Model):
    """Anggota tim visitasi lapangan."""

    ROLE_CHOICES = [
        ('ketua_tim', 'Ketua Tim'),
        ('anggota', 'Anggota'),
        ('notulis', 'Notulis'),
        ('pendamping_lp3m', 'Pendamping LP3M'),
    ]

    visitasi = models.ForeignKey(Visitasi, on_delete=models.CASCADE, related_name='anggota_set')
    user = models.ForeignKey(UserAmi, on_delete=models.PROTECT, related_name='visitasi_anggota_set')

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    konflik_kepentingan = models.TextField(null=True, blank=True)

    is_hadir = models.BooleanField(default=False)
    waktu_hadir = models.DateTimeField(null=True, blank=True)
    waktu_pulang = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visitasi_anggota'
        verbose_name = 'Anggota Visitasi'
        verbose_name_plural = 'Anggota Visitasi'
        constraints = [
            models.UniqueConstraint(fields=['visitasi', 'user'], name='uniq_visitasi_anggota_user'),
        ]

    def __str__(self):
        return f'{self.user} — {self.get_role_display()}'


class VisitasiAgenda(models.Model):
    """Sesi/agenda dalam pelaksanaan visitasi (opening, wawancara, observasi, FGD, closing)."""

    STATUS_CHOICES = [
        ('belum_mulai', 'Belum Mulai'),
        ('sedang_berlangsung', 'Sedang Berlangsung'),
        ('selesai', 'Selesai'),
        ('dilewati', 'Dilewati'),
    ]

    visitasi = models.ForeignKey(Visitasi, on_delete=models.CASCADE, related_name='agenda_set')

    no_urut = models.PositiveIntegerField()
    waktu_mulai = models.TimeField()
    waktu_selesai = models.TimeField()
    judul_sesi = models.CharField(max_length=200)
    deskripsi = models.TextField(null=True, blank=True)
    pic = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='agenda_pic_set',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='belum_mulai')

    notulen_sesi = models.TextField(null=True, blank=True)
    foto_dokumentasi = models.JSONField(null=True, blank=True, help_text='Array URL foto')

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visitasi_agenda'
        verbose_name = 'Agenda Visitasi'
        verbose_name_plural = 'Agenda Visitasi'
        ordering = ['visitasi', 'no_urut']

    def __str__(self):
        return f'{self.judul_sesi} ({self.visitasi})'
