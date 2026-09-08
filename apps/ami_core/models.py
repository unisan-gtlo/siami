from django.db import models
from django.db.models import Q


class RegulasiAcuan(models.Model):
    """Sumber kebenaran tunggal untuk rujukan peraturan penjaminan mutu.

    Permendikbudristek 53/2023 dicabut oleh Permendiktisaintek 39/2025
    (Pasal 117) -- baris 53/2023 dipertahankan berstatus 'dicabut' agar
    siklus AMI lama tetap mencetak rujukan yang benar untuk zamannya.
    """

    STATUS_CHOICES = [
        ('berlaku', 'Berlaku'),
        ('dicabut', 'Dicabut'),
    ]

    kode = models.CharField(max_length=30, unique=True)
    nama_lengkap = models.TextField()
    nama_pendek = models.CharField(max_length=100)
    berita_negara = models.CharField(max_length=100, null=True, blank=True)

    tanggal_tetap = models.DateField(null=True, blank=True)
    tanggal_undang = models.DateField(null=True, blank=True)

    mencabut = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dicabut_oleh_set',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='berlaku')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'regulasi_acuan'
        verbose_name = 'Regulasi Acuan'
        verbose_name_plural = 'Regulasi Acuan'

    def __str__(self):
        return self.nama_pendek


class Siklus(models.Model):
    """Siklus AMI (UNISAN saat ini di Siklus 8, 2025/2026)."""

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    no_siklus = models.PositiveIntegerField(unique=True)
    nama = models.CharField(max_length=50)
    tahun_akademik = models.CharField(max_length=20)

    tgl_mulai = models.DateField()
    tgl_selesai = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    is_current = models.BooleanField(default=False)

    sk_rektor_no = models.CharField(max_length=100, null=True, blank=True)
    sk_rektor_tgl = models.DateField(null=True, blank=True)
    sk_rektor_file = models.CharField(max_length=500, null=True, blank=True)

    regulasi_acuan = models.ForeignKey(
        RegulasiAcuan, on_delete=models.SET_NULL, null=True, blank=True, related_name='siklus_set',
        help_text='Peraturan penjaminan mutu yang berlaku saat siklus ini dilaksanakan.',
    )

    konfig = models.JSONField(null=True, blank=True)

    closing_date = models.DateField(null=True, blank=True)
    closing_notulen_file = models.CharField(max_length=500, null=True, blank=True)

    keterangan = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siklus'
        verbose_name_plural = 'Siklus'
        ordering = ['-no_siklus']
        constraints = [
            models.UniqueConstraint(
                fields=['is_current'], condition=Q(is_current=True),
                name='uniq_siklus_current',
            ),
        ]

    def __str__(self):
        return self.nama


class Tahap(models.Model):
    """3 tahap pelaksanaan AMI: AMI Online, Desk Evaluasi, Visitasi Lapangan."""

    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    no_urut = models.PositiveSmallIntegerField()
    deskripsi = models.TextField(null=True, blank=True)
    durasi_hari = models.PositiveIntegerField(null=True, blank=True)
    is_aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'tahap'
        verbose_name_plural = 'Tahap'
        ordering = ['no_urut']

    def __str__(self):
        return self.nama


class Standar(models.Model):
    """9 Standar SN-Dikti yang menjadi acuan AMI."""

    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    nama_pendek = models.CharField(max_length=50)
    deskripsi = models.TextField(null=True, blank=True)
    no_urut = models.PositiveSmallIntegerField()
    warna_hex = models.CharField(max_length=7, default='#1B7BB8')
    is_aktif = models.BooleanField(default=True)

    class Meta:
        db_table = 'standar'
        verbose_name_plural = 'Standar'
        ordering = ['no_urut']

    def __str__(self):
        return f'{self.kode}. {self.nama_pendek}'


class ButirPenilaian(models.Model):
    """62 butir penilaian per siklus AMI berdasarkan SN-Dikti."""

    JENIS_INPUT_CHOICES = [
        ('numerik', 'Numerik'),
        ('rasio', 'Rasio'),
        ('persentase', 'Persentase'),
        ('pilihan', 'Pilihan'),
        ('narasi', 'Narasi'),
        ('tabel_dinamis', 'Tabel Dinamis'),
        ('auto_iku', 'Auto IKU'),
    ]
    OPERATOR_TARGET_CHOICES = [
        ('>=', '>='),
        ('<=', '<='),
        ('=', '='),
        ('>', '>'),
        ('<', '<'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='butir_set')
    standar = models.ForeignKey(Standar, on_delete=models.PROTECT, related_name='butir_set')

    kode = models.CharField(max_length=20)
    judul = models.CharField(max_length=300)
    deskripsi = models.TextField(null=True, blank=True)

    jenis_input = models.CharField(max_length=30, choices=JENIS_INPUT_CHOICES)

    target_iku = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    target_satuan = models.CharField(max_length=50, null=True, blank=True)
    operator_target = models.CharField(
        max_length=5, choices=OPERATOR_TARGET_CHOICES, null=True, blank=True,
    )

    auto_source_schema = models.CharField(max_length=20, null=True, blank=True)
    auto_source_table = models.CharField(max_length=50, null=True, blank=True)
    auto_query_template = models.TextField(null=True, blank=True)

    bobot = models.PositiveIntegerField(default=1)
    is_wajib = models.BooleanField(default=True)
    is_kuantitatif = models.BooleanField(default=False)

    panduan_pengisian = models.TextField(null=True, blank=True)
    rujukan_dokumen = models.CharField(max_length=500, null=True, blank=True)
    rujukan_sn_dikti = models.CharField(max_length=200, null=True, blank=True)

    no_urut = models.PositiveIntegerField()
    is_aktif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'butir_penilaian'
        verbose_name_plural = 'Butir Penilaian'
        ordering = ['siklus', 'standar', 'no_urut']
        constraints = [
            models.UniqueConstraint(
                fields=['siklus', 'kode'], name='uniq_butir_siklus_kode',
            ),
        ]

    def __str__(self):
        return f'{self.kode} — {self.judul}'
