from django.db import models

from apps.ami_assessment.models import JawabanButir, Pengisian
from apps.ami_core.models import ButirPenilaian, Siklus
from apps.ami_user.models import UserAmi


class DePenugasan(models.Model):
    """SK Penugasan Auditor Desk Evaluasi — 1 prodi bisa punya beberapa auditor."""

    ROLE_CHOICES = [
        ('ketua_tim', 'Ketua Tim'),
        ('auditor', 'Auditor'),
        ('pendamping', 'Pendamping'),
    ]
    STATUS_CHOICES = [
        ('ditugaskan', 'Ditugaskan'),
        ('dimulai', 'Dimulai'),
        ('on_progress', 'On Progress'),
        ('selesai_de', 'Selesai DE'),
        ('difinalisasi', 'Difinalisasi'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='de_penugasan_set')
    pengisian = models.ForeignKey(
        Pengisian, on_delete=models.PROTECT, related_name='de_penugasan_set',
        help_text='Auditee (self-assessment yang dinilai)',
    )
    auditor = models.ForeignKey(
        UserAmi, on_delete=models.PROTECT, related_name='de_penugasan_set',
    )
    role_dalam_tim = models.CharField(max_length=20, choices=ROLE_CHOICES, default='auditor')

    sk_no = models.CharField(max_length=100)
    sk_tgl = models.DateField()
    sk_file = models.CharField(max_length=500, null=True, blank=True)

    tgl_mulai_de = models.DateField()
    tenggat_de = models.DateField()
    tgl_selesai_aktual = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='ditugaskan')

    total_butir = models.PositiveIntegerField(default=0)
    butir_dinilai = models.PositiveIntegerField(default=0)
    butir_skor_1 = models.PositiveIntegerField(default=0)
    butir_skor_0 = models.PositiveIntegerField(default=0)

    konflik_kepentingan_signed = models.BooleanField(default=False)
    konflik_kepentingan_signed_at = models.DateTimeField(null=True, blank=True)

    catatan_lp3m = models.TextField(null=True, blank=True)
    catatan_auditor = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'de_penugasan'
        verbose_name = 'Penugasan DE'
        verbose_name_plural = 'Penugasan DE'
        ordering = ['-siklus', 'tenggat_de']
        constraints = [
            models.UniqueConstraint(
                fields=['pengisian', 'auditor'], name='uniq_de_penugasan_pengisian_auditor',
            ),
        ]

    def __str__(self):
        return f'{self.pengisian.prodi} — {self.auditor} ({self.get_status_display()})'


def hitung_klasifikasi(skor, butir_kritis=False):
    """Konversi skor rubrik 0-4 -> klasifikasi temuan, mengikuti tabel
    konversi spesifikasi-modul-kelola-instrumen.md bagian 3. Butir kritis
    dengan skor<3 selalu KTS_MAYOR, mengabaikan tabel dasar (butir kritis
    tidak boleh diturunkan jadi KTS Minor)."""
    if skor is None:
        return None
    if butir_kritis and skor < 3:
        return 'KTS_MAYOR'
    return {4: 'SESUAI', 3: 'OB', 2: 'KTS_MINOR', 1: 'KTS_MAYOR', 0: 'KTS_MAYOR'}.get(skor)


class DePenilaian(models.Model):
    """Penilaian Desk Evaluasi per butir — skor rubrik 0-4 + framework PLOR.

    Jantung sistem AMI. Skor 0-4 (Permendiktisaintek 39/2025, lihat
    spesifikasi-modul-kelola-instrumen.md): 4=Sangat Baik/Melampaui,
    3=Baik/Terpenuhi, 2=Cukup, 1=Kurang, 0=Tidak Ada. Klasifikasi
    diturunkan dari skor lewat hitung_klasifikasi(), bukan dipilih manual.
    """

    KLASIFIKASI_CHOICES = [
        ('SESUAI', 'Sesuai (Conformity)'),
        ('OB', 'Observasi (OB)'),
        ('KTS_MINOR', 'Ketidaksesuaian Minor (KTS Minor)'),
        ('KTS_MAYOR', 'Ketidaksesuaian Mayor (KTS Mayor)'),
        # Legacy -- nilai lama, tidak dipakai untuk baris baru, dipertahankan
        # supaya tampilan tidak error bila suatu saat ada baris lama.
        ('KTB', 'Ketidaksesuaian Berat (legacy)'),
        ('KTS', 'Ketidaksesuaian Sedang (legacy)'),
        ('BP', 'Best Practice (legacy)'),
    ]
    SKOR_CHOICES = [
        (0, '0 — Tidak Ada'),
        (1, '1 — Kurang'),
        (2, '2 — Cukup'),
        (3, '3 — Baik / Terpenuhi'),
        (4, '4 — Sangat Baik / Melampaui'),
    ]

    penugasan = models.ForeignKey(
        DePenugasan, on_delete=models.CASCADE, related_name='penilaian_set',
    )
    butir = models.ForeignKey(
        ButirPenilaian, on_delete=models.PROTECT, related_name='de_penilaian_set',
    )
    jawaban = models.ForeignKey(
        JawabanButir, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='de_penilaian_set', help_text='Link ke jawaban auditee',
    )

    skor = models.PositiveSmallIntegerField(null=True, blank=True, choices=SKOR_CHOICES)
    klasifikasi = models.CharField(max_length=10, choices=KLASIFIKASI_CHOICES, null=True, blank=True)

    plor_problem = models.TextField(null=True, blank=True, verbose_name='PLOR — Problem')
    plor_location = models.CharField(max_length=300, null=True, blank=True, verbose_name='PLOR — Location')
    plor_objective = models.CharField(max_length=500, null=True, blank=True, verbose_name='PLOR — Objective')
    plor_reference = models.CharField(max_length=500, null=True, blank=True, verbose_name='PLOR — Reference')

    catatan_auditor = models.TextField(null=True, blank=True)
    rekomendasi_visitasi = models.TextField(null=True, blank=True)

    dokumen_diperiksa = models.JSONField(
        null=True, blank=True, help_text='Array id DokumenBukti yang diperiksa',
    )

    is_draft = models.BooleanField(default=True)
    is_finalisasi = models.BooleanField(default=False)

    dinilai_pada = models.DateTimeField(null=True, blank=True)
    difinalisasi_pada = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'de_penilaian'
        verbose_name = 'Penilaian DE'
        verbose_name_plural = 'Penilaian DE'
        constraints = [
            models.CheckConstraint(
                check=models.Q(skor__in=[0, 1, 2, 3, 4]) | models.Q(skor__isnull=True),
                name='chk_de_penilaian_skor_0_4',
            ),
            models.UniqueConstraint(
                fields=['penugasan', 'butir'], name='uniq_de_penilaian_penugasan_butir',
            ),
        ]

    def __str__(self):
        return f'{self.penugasan} — {self.butir.kode} (skor={self.skor})'


class DeDaftarTilik(models.Model):
    """Daftar tilik output DE — panduan verifikasi auditor visitasi."""

    PRIORITAS_CHOICES = [
        ('tinggi', 'Tinggi'),
        ('sedang', 'Sedang'),
        ('rendah', 'Rendah'),
    ]
    METODE_CHOICES = [
        ('wawancara', 'Wawancara'),
        ('observasi', 'Observasi'),
        ('review_dokumen', 'Review Dokumen'),
        ('fgd', 'FGD'),
        ('inspeksi_lapangan', 'Inspeksi Lapangan'),
    ]
    STATUS_VISITASI_CHOICES = [
        ('belum_diperiksa', 'Belum Diperiksa'),
        ('terkonfirmasi', 'Terkonfirmasi'),
        ('tidak_terkonfirmasi', 'Tidak Terkonfirmasi'),
        ('perlu_followup', 'Perlu Follow-up'),
    ]

    penugasan = models.ForeignKey(
        DePenugasan, on_delete=models.CASCADE, related_name='daftar_tilik_set',
    )
    butir = models.ForeignKey(
        ButirPenilaian, on_delete=models.PROTECT, related_name='daftar_tilik_set',
    )
    penilaian = models.ForeignKey(
        DePenilaian, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='daftar_tilik_set',
    )

    deskripsi_tilik = models.TextField()
    prioritas = models.CharField(max_length=10, choices=PRIORITAS_CHOICES, null=True, blank=True)
    metode_verifikasi = models.CharField(max_length=30, choices=METODE_CHOICES, null=True, blank=True)

    sasaran_pic = models.CharField(max_length=200, null=True, blank=True)

    status_visitasi = models.CharField(
        max_length=20, choices=STATUS_VISITASI_CHOICES, default='belum_diperiksa',
    )
    catatan_visitasi = models.TextField(null=True, blank=True)
    diperiksa_oleh = models.ForeignKey(
        UserAmi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tilik_diperiksa_set',
    )
    diperiksa_pada = models.DateTimeField(null=True, blank=True)

    no_urut = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'de_daftar_tilik'
        verbose_name = 'Daftar Tilik DE'
        verbose_name_plural = 'Daftar Tilik DE'
        ordering = ['penugasan', 'no_urut']

    def __str__(self):
        return self.deskripsi_tilik[:80]
