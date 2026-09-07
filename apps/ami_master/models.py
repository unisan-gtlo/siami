from django.db import models


class Fakultas(models.Model):
    """Master data fakultas — mirror dari schema akademik, di-sync nightly.

    managed=False: tabel & trigger sudah dibuat lewat 01_database/02_tables_master.sql,
    Django hanya merepresentasikan skema yang ada, tidak mengelola DDL-nya.
    """

    id = models.AutoField(primary_key=True)  # kolom asli: SERIAL (int4)
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=150)
    nama_singkat = models.CharField(max_length=20)

    dekan_user_id = models.IntegerField(null=True, blank=True)
    upm_user_id = models.IntegerField(null=True, blank=True)

    alamat = models.TextField(null=True, blank=True)
    telp = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)

    is_aktif = models.BooleanField(default=True)

    source_schema = models.CharField(max_length=20, default='akademik')
    source_id = models.IntegerField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'fakultas'
        verbose_name_plural = 'Fakultas'
        ordering = ['nama']

    def __str__(self):
        return self.nama_singkat


class Prodi(models.Model):
    """Master data program studi — sumber utama auditee dalam AMI."""

    STRATA_CHOICES = [
        ('D3', 'D3'),
        ('D4', 'D4'),
        ('S1', 'S1'),
        ('S2', 'S2'),
        ('S3', 'S3'),
        ('Profesi', 'Profesi'),
    ]
    AKREDITASI_LEMBAGA_CHOICES = [
        ('BAN-PT', 'BAN-PT'),
        ('LAM-PTKes', 'LAM-PTKes'),
        ('LAMSAMA', 'LAMSAMA'),
        ('LAMINFOKOM', 'LAMINFOKOM'),
        ('LAM-Teknik', 'LAM-Teknik'),
        ('Belum', 'Belum'),
    ]
    AKREDITASI_PERINGKAT_CHOICES = [
        ('Unggul', 'Unggul'),
        ('Baik Sekali', 'Baik Sekali'),
        ('Baik', 'Baik'),
        ('Terakreditasi', 'Terakreditasi'),
        ('Belum', 'Belum'),
    ]

    id = models.AutoField(primary_key=True)  # kolom asli: SERIAL (int4)
    fakultas = models.ForeignKey(
        Fakultas, on_delete=models.PROTECT, db_column='fakultas_id',
        related_name='prodi_set',
    )
    kode = models.CharField(max_length=20, unique=True)
    kode_pddikti = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nama = models.CharField(max_length=200)
    nama_inggris = models.CharField(max_length=200, null=True, blank=True)
    strata = models.CharField(max_length=10, choices=STRATA_CHOICES)

    kaprodi_user_id = models.IntegerField(null=True, blank=True)
    sekprodi_user_id = models.IntegerField(null=True, blank=True)

    sk_pendirian_no = models.CharField(max_length=100, null=True, blank=True)
    sk_pendirian_tgl = models.DateField(null=True, blank=True)
    sk_pendirian_file = models.CharField(max_length=500, null=True, blank=True)

    akreditasi_lembaga = models.CharField(
        max_length=20, choices=AKREDITASI_LEMBAGA_CHOICES, null=True, blank=True,
    )
    akreditasi_peringkat = models.CharField(
        max_length=20, choices=AKREDITASI_PERINGKAT_CHOICES, null=True, blank=True,
    )
    akreditasi_no_sk = models.CharField(max_length=100, null=True, blank=True)
    akreditasi_tgl_sk = models.DateField(null=True, blank=True)
    akreditasi_berlaku_sd = models.DateField(null=True, blank=True)

    is_aktif = models.BooleanField(default=True)

    source_schema = models.CharField(max_length=20, default='akademik')
    source_id = models.IntegerField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'prodi'
        verbose_name_plural = 'Prodi'
        ordering = ['nama']

    def __str__(self):
        return f'{self.kode} — {self.nama}'
