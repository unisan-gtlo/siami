from django.db import models


class Fakultas(models.Model):
    """Master data fakultas — cache lokal, di-sync berkala dari SIAKAD via API."""

    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=150)
    nama_singkat = models.CharField(max_length=20)

    dekan_user_id = models.IntegerField(null=True, blank=True)
    upm_user_id = models.IntegerField(null=True, blank=True)

    alamat = models.TextField(null=True, blank=True)
    telp = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)

    is_aktif = models.BooleanField(default=True)

    source_schema = models.CharField(max_length=20, default='master')
    source_id = models.CharField(max_length=50, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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
    # Diperbarui 8 Sep 2026 -- daftar 7 LAM resmi yang sudah beroperasi
    # (di luar BAN-PT), diverifikasi lewat pencarian web karena ekosistem
    # LAM terus bertambah (LAMSPAK misalnya baru beroperasi 22 Jan 2025).
    # Humaniora/keagamaan per info terkini masih ditangani BAN-PT langsung,
    # belum punya LAM sendiri.
    AKREDITASI_LEMBAGA_CHOICES = [
        ('BAN-PT', 'BAN-PT'),
        ('LAM-PTKes', 'LAM-PTKes'),
        ('LAM-Teknik', 'LAM-Teknik'),
        ('LAMDIK', 'LAMDIK (Kependidikan)'),
        ('LAMINFOKOM', 'LAMINFOKOM'),
        ('LAMSAMA', 'LAMSAMA'),
        ('LAMEMBA', 'LAMEMBA (Ekonomi, Manajemen, Bisnis, Akuntansi)'),
        ('LAMSPAK', 'LAMSPAK (Sosial, Politik, Administrasi, Komunikasi)'),
        ('Belum', 'Belum'),
    ]
    AKREDITASI_PERINGKAT_CHOICES = [
        ('Unggul', 'Unggul'),
        ('Baik Sekali', 'Baik Sekali'),
        ('Baik', 'Baik'),
        ('Terakreditasi', 'Terakreditasi'),
        ('A', 'A (skema lama)'),
        ('B', 'B (skema lama)'),
        ('C', 'C (skema lama)'),
        ('Belum', 'Belum'),
    ]
    # Status siklus-hidup akreditasi (Permendiktisaintek 39/2025 Pasal 70
    # ayat 4, Pasal 76) -- BERBEDA dari akreditasi_peringkat di atas (yang
    # itu soal nilai/grade B/Baik/Unggul dst). Field ini soal: prodi ini
    # sudah pernah diakreditasi atau belum, dan berhak meluluskan mahasiswa
    # atau tidak.
    STATUS_AKREDITASI_CHOICES = [
        ('tidak_terakreditasi', 'Tidak Terakreditasi'),
        ('terakreditasi_pertama', 'Terakreditasi Pertama'),
        ('terakreditasi', 'Terakreditasi'),
        ('terakreditasi_unggul', 'Terakreditasi Unggul'),
        # Legacy -- nomenklatur 53/2023 (Pasal 77 ayat 2), dipertahankan
        # sebagai nilai tampil sesuai Pasal 114 ayat (1) huruf a, TIDAK
        # dipakai untuk data baru.
        ('terakreditasi_sementara', 'Terakreditasi Sementara (nomenklatur lama)'),
    ]

    fakultas = models.ForeignKey(
        Fakultas, on_delete=models.PROTECT, related_name='prodi_set',
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

    tanggal_mulai_beroperasi = models.DateField(
        null=True, blank=True,
        help_text='Dasar hitung tenggat wajib ajukan akreditasi 2 tahun (Permendiktisaintek 39/2025 Pasal 77 ayat 1).',
    )

    akreditasi_lembaga = models.CharField(
        max_length=20, choices=AKREDITASI_LEMBAGA_CHOICES, null=True, blank=True,
    )
    akreditasi_peringkat = models.CharField(
        max_length=20, choices=AKREDITASI_PERINGKAT_CHOICES, null=True, blank=True,
    )
    akreditasi_no_sk = models.CharField(max_length=100, null=True, blank=True)
    akreditasi_tgl_sk = models.DateField(null=True, blank=True)
    akreditasi_berlaku_sd = models.DateField(null=True, blank=True)

    status_akreditasi = models.CharField(
        max_length=25, choices=STATUS_AKREDITASI_CHOICES, null=True, blank=True,
        help_text='Syarat kelayakan meluluskan mahasiswa/menerbitkan ijazah (Pasal 70 ayat 4).',
    )
    status_asal = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Jejak audit: nilai akreditasi_peringkat sebelum status_akreditasi diisi eksplisit pertama kali.',
    )

    is_aktif = models.BooleanField(default=True)

    source_schema = models.CharField(max_length=20, default='master')
    source_id = models.CharField(max_length=50, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prodi'
        verbose_name_plural = 'Prodi'
        ordering = ['nama']

    def __str__(self):
        return f'{self.kode} — {self.nama}'

    def kelayakan_ijazah(self):
        return kelayakan_ijazah(self.status_akreditasi)


STATUS_LAYAK_IJAZAH = {'terakreditasi_pertama', 'terakreditasi', 'terakreditasi_unggul'}


def kelayakan_ijazah(status_akreditasi):
    """Pasal 70 ayat (4) Permendiktisaintek 39/2025: prodi wajib berstatus
    terakreditasi_pertama, terakreditasi, atau terakreditasi_unggul untuk
    berhak meluluskan mahasiswa dan menerbitkan ijazah.

    Mengembalikan (layak: bool, peringatan: str atau None). Status kosong
    atau tidak_terakreditasi TIDAK memblokir apa pun secara otomatis di
    portal ini (sistem ini tidak punya alur penerbitan ijazah) -- fungsi
    ini murni indikator untuk LP3M/prodi, bukan gerbang teknis.

    TODO(verifikasi-LP3M): 53/2023 Pasal 88 juga mengizinkan status
    "terakreditasi secara internasional"; istilah itu tidak lagi disebut
    eksplisit di 39/2025 Pasal 70 ayat (4) (keyakinan brief migrasi:
    Sedang -- lihat MIGRASI-PERMEN-39-2025.md butir C4). Portal ini tidak
    melacak kategori akreditasi internasional secara terpisah, jadi
    ambiguitas itu untuk saat ini tidak berdampak pada logika di bawah.
    """
    if status_akreditasi in STATUS_LAYAK_IJAZAH:
        return True, None
    if status_akreditasi == 'terakreditasi_sementara':
        return True, (
            'Status ini nomenklatur lama (Permendikbudristek 53/2023). '
            'Perbarui ke "Terakreditasi Pertama" sesuai Permendiktisaintek 39/2025 Pasal 76.'
        )
    if status_akreditasi == 'tidak_terakreditasi':
        return False, 'Status akreditasi tidak memenuhi syarat Pasal 70 ayat (4) untuk meluluskan mahasiswa/menerbitkan ijazah.'
    return False, 'Status akreditasi belum diisi.'
