from django.db import models

from apps.ami_core.models import Siklus
from apps.ami_user.models import UserAmi


class Rtm(models.Model):
    """Rapat Tinjauan Manajemen pasca-AMI per siklus."""

    STATUS_CHOICES = [
        ('terjadwal', 'Terjadwal'),
        ('sedang_berlangsung', 'Sedang Berlangsung'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='rtm_set')

    judul = models.CharField(max_length=300)
    tgl_rapat = models.DateField()
    waktu_mulai = models.TimeField(null=True, blank=True)
    waktu_selesai = models.TimeField(null=True, blank=True)
    tempat = models.CharField(max_length=300, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='terjadwal')

    pemimpin = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='rtm_pemimpin_set',
    )
    notulis = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='rtm_notulis_set',
    )

    notulen_file = models.CharField(max_length=500, null=True, blank=True)
    sk_keputusan_file = models.CharField(max_length=500, null=True, blank=True)
    foto_dokumentasi = models.JSONField(null=True, blank=True)

    jml_peserta = models.PositiveIntegerField(default=0)
    jml_keputusan = models.PositiveIntegerField(default=0)
    jml_action_item = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rtm'
        verbose_name = 'RTM'
        verbose_name_plural = 'RTM'
        ordering = ['-tgl_rapat']

    def __str__(self):
        return f'{self.judul} — {self.tgl_rapat}'


class RtmAgenda(models.Model):
    """Agenda keputusan strategis dalam RTM."""

    PRIORITAS_CHOICES = [
        ('rendah', 'Rendah'),
        ('sedang', 'Sedang'),
        ('tinggi', 'Tinggi'),
        ('kritis', 'Kritis'),
    ]
    KEPUTUSAN_CHOICES = [
        ('pending', 'Pending'),
        ('disetujui', 'Disetujui'),
        ('ditolak', 'Ditolak'),
        ('ditunda', 'Ditunda'),
    ]

    rtm = models.ForeignKey(Rtm, on_delete=models.CASCADE, related_name='agenda_set')

    no_urut = models.PositiveIntegerField()
    judul = models.CharField(max_length=300)
    deskripsi = models.TextField(null=True, blank=True)

    prioritas = models.CharField(max_length=20, choices=PRIORITAS_CHOICES, null=True, blank=True)

    estimasi_anggaran = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sumber_anggaran = models.CharField(max_length=200, null=True, blank=True)

    pic = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='rtm_agenda_pic_set',
    )
    pic_unit = models.CharField(max_length=200, null=True, blank=True)
    target_completion = models.DateField(null=True, blank=True)

    is_voting_enabled = models.BooleanField(default=False)
    voting_setuju = models.PositiveIntegerField(default=0)
    voting_tidak = models.PositiveIntegerField(default=0)
    voting_abstain = models.PositiveIntegerField(default=0)

    keputusan = models.CharField(max_length=20, choices=KEPUTUSAN_CHOICES, null=True, blank=True)
    keputusan_pada = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rtm_agenda'
        verbose_name = 'Agenda RTM'
        verbose_name_plural = 'Agenda RTM'
        ordering = ['rtm', 'no_urut']

    def __str__(self):
        return self.judul


class RtmNotulen(models.Model):
    """Notulen RTM real-time collaborative (chat-style)."""

    TIPE_CHOICES = [
        ('komentar', 'Komentar'),
        ('pertanyaan', 'Pertanyaan'),
        ('usulan', 'Usulan'),
        ('action_item', 'Action Item'),
        ('keputusan', 'Keputusan'),
        ('sistem', 'Sistem'),
    ]
    ACTION_STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]

    rtm = models.ForeignKey(Rtm, on_delete=models.CASCADE, related_name='notulen_set')
    user = models.ForeignKey(UserAmi, on_delete=models.PROTECT, related_name='rtm_notulen_set')
    isi = models.TextField()

    tipe = models.CharField(max_length=20, choices=TIPE_CHOICES, default='komentar')

    is_action_item = models.BooleanField(default=False)
    action_pic = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True, related_name='rtm_action_pic_set',
    )
    action_deadline = models.DateField(null=True, blank=True)
    action_status = models.CharField(max_length=20, choices=ACTION_STATUS_CHOICES, null=True, blank=True)

    waktu_kirim = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reply_set',
    )

    class Meta:
        db_table = 'rtm_notulen'
        verbose_name = 'Notulen RTM'
        verbose_name_plural = 'Notulen RTM'
        ordering = ['rtm', 'waktu_kirim']

    def __str__(self):
        return f'{self.user}: {self.isi[:50]}'


class RtmVote(models.Model):
    """Satu suara satu peserta per agenda RTM — mencegah vote ganda."""

    PILIHAN_CHOICES = [
        ('setuju', 'Setuju'),
        ('tidak', 'Tidak Setuju'),
        ('abstain', 'Abstain'),
    ]

    agenda = models.ForeignKey(RtmAgenda, on_delete=models.CASCADE, related_name='vote_set')
    user = models.ForeignKey(UserAmi, on_delete=models.CASCADE, related_name='rtm_vote_set')
    pilihan = models.CharField(max_length=10, choices=PILIHAN_CHOICES)

    voted_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rtm_vote'
        verbose_name = 'Vote RTM'
        verbose_name_plural = 'Vote RTM'
        constraints = [
            models.UniqueConstraint(fields=['agenda', 'user'], name='uniq_rtm_vote_agenda_user'),
        ]

    def __str__(self):
        return f'{self.user} — {self.agenda} — {self.get_pilihan_display()}'
