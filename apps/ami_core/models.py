from django.contrib.postgres.fields import ArrayField
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


class RefEnumerasi(models.Model):
    """Tabel referensi generik untuk nilai enumerasi modul Kelola Instrumen
    (Domain, Kelompok Standar, Metode Verifikasi, Sumber Data, Tahap Audit,
    Lapis Audit, Sasaran Auditee, Jenis Jawaban, Klasifikasi Temuan, Status
    Butir) -- sesuai `ref-enumerasi.csv` LP3M. Sengaja satu tabel generik,
    bukan satu tabel per kelompok, karena isinya murni lookup statis kecil.
    """

    kelompok = models.CharField(max_length=50)
    kode = models.CharField(max_length=20)
    nilai = models.CharField(max_length=200)
    domain_induk = models.CharField(max_length=150, null=True, blank=True)
    keterangan = models.TextField(null=True, blank=True)
    no_urut = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'ref_enumerasi'
        verbose_name = 'Referensi Enumerasi'
        verbose_name_plural = 'Referensi Enumerasi'
        ordering = ['kelompok', 'no_urut']
        constraints = [
            models.UniqueConstraint(fields=['kelompok', 'kode'], name='uniq_ref_enumerasi_kelompok_kode'),
        ]

    def __str__(self):
        return f'{self.kelompok}/{self.kode} — {self.nilai}'


class MasterStandar(models.Model):
    """18 Master Standar SN-Dikti (Permendiktisaintek 39/2025 Pasal 5-64)
    berjenjang Domain > Kelompok Standar > Standar -- terpisah dari model
    `Standar` yang sudah ada (taksonomi institusional UNISAN sendiri, bukan
    taksonomi Pasal 5 SN-Dikti). Keduanya hidup berdampingan.
    """

    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=200)
    domain_induk = models.CharField(max_length=150, null=True, blank=True)
    keterangan = models.CharField(max_length=200, null=True, blank=True, help_text='Rujukan pasal.')
    no_urut = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'master_standar'
        verbose_name = 'Master Standar'
        verbose_name_plural = 'Master Standar'
        ordering = ['no_urut']

    def __str__(self):
        return f'{self.kode} — {self.nama}'


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
    DOMAIN_CHOICES = [
        ('PDD', 'Pendidikan'),
        ('PNL', 'Penelitian'),
        ('PKM', 'Pengabdian kepada Masyarakat'),
        ('NAK', 'Nonakademik'),
    ]
    KELOMPOK_STANDAR_CHOICES = [
        ('L', 'Luaran'),
        ('P', 'Proses'),
        ('M', 'Masukan'),
        ('T', 'Tata Kelola SPMI'),
    ]
    SUMBER_DATA_CHOICES = [
        ('SD-1', 'PD Dikti'),
        ('SD-2', 'SIMAK / SIA UNISAN'),
        ('SD-3', 'Dokumen Prodi'),
        ('SD-4', 'Dokumen UPPS/Fakultas'),
        ('SD-5', 'Dokumen Universitas'),
        ('SD-6', 'Survei / Tracer Study'),
    ]
    TAHAP_AUDIT_CHOICES = [
        ('TA-1', 'Desk Evaluasi (Audit Sistem)'),
        ('TA-2', 'Audit Lapangan (Audit Kepatuhan)'),
        ('TA-3', 'Keduanya'),
    ]
    LAPIS_AUDIT_CHOICES = [
        ('kepatuhan', 'Kepatuhan SN Dikti'),
        ('pelampauan', 'Pelampauan (Unggul)'),
    ]
    JENIS_JAWABAN_CHOICES = [
        ('JJ-1', 'Skala 0-4'),
        ('JJ-2', 'Ya / Tidak'),
        ('JJ-3', 'Numerik'),
        ('JJ-4', 'Persentase'),
        ('JJ-5', 'Uraian + Bukti'),
    ]
    STATUS_CHOICES = [
        ('draf', 'Draf'),
        ('aktif', 'Aktif'),
        ('nonaktif', 'Nonaktif'),
        ('diarsipkan', 'Diarsipkan'),
    ]

    siklus = models.ForeignKey(Siklus, on_delete=models.PROTECT, related_name='butir_set')
    standar = models.ForeignKey(Standar, on_delete=models.PROTECT, related_name='butir_set')
    master_standar = models.ForeignKey(
        MasterStandar, on_delete=models.SET_NULL, null=True, blank=True, related_name='butir_set',
        help_text='Pemetaan ke taksonomi Pasal 5 SN-Dikti (39/2025). Boleh kosong untuk butir lama.',
    )

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
    rujukan_sn_dikti = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Deprecated -- dipertahankan untuk kompatibilitas lama, gunakan dasar_hukum.',
    )

    # --- Field spesifikasi Kelola Instrumen (Permendiktisaintek 39/2025) ---
    domain = models.CharField(max_length=5, choices=DOMAIN_CHOICES, null=True, blank=True)
    kelompok_standar = models.CharField(max_length=2, choices=KELOMPOK_STANDAR_CHOICES, null=True, blank=True)
    sub_standar = models.CharField(max_length=150, null=True, blank=True)
    pernyataan_butir = models.TextField(
        null=True, blank=True, help_text='Pernyataan auditable (dapat dijawab terpenuhi/tidak).',
    )
    indikator_ketercapaian = models.TextField(null=True, blank=True)
    dasar_hukum = ArrayField(models.CharField(max_length=300), null=True, blank=True)
    dokumen_bukti_wajib = models.JSONField(
        null=True, blank=True, help_text='Daftar [{"nama": "...", "wajib": true}, ...].',
    )
    metode_verifikasi = ArrayField(models.CharField(max_length=10), null=True, blank=True)
    sumber_data = models.CharField(max_length=10, choices=SUMBER_DATA_CHOICES, null=True, blank=True)
    tahap_audit = models.CharField(max_length=10, choices=TAHAP_AUDIT_CHOICES, null=True, blank=True)
    lapis_audit = models.CharField(max_length=20, choices=LAPIS_AUDIT_CHOICES, default='kepatuhan')
    sasaran_auditee = ArrayField(models.CharField(max_length=10), null=True, blank=True)
    jenis_jawaban = models.CharField(max_length=10, choices=JENIS_JAWABAN_CHOICES, null=True, blank=True)
    rubrik_skor = models.JSONField(
        null=True, blank=True, help_text='Daftar [{"skor": 0-4, "deskripsi": "..."}, ...].',
    )
    butir_kritis = models.BooleanField(default=False)
    kaitan_akreditasi = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    versi = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        'ami_user.UserAmi', on_delete=models.SET_NULL, null=True, blank=True, related_name='butir_created_set',
    )
    updated_by = models.ForeignKey(
        'ami_user.UserAmi', on_delete=models.SET_NULL, null=True, blank=True, related_name='butir_updated_set',
    )

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

    def save(self, *args, **kwargs):
        # `is_aktif` boolean sudah dipakai luas di query lain (ami_de,
        # ami_assessment) -- disinkronkan otomatis dari `status` yang lebih
        # kaya supaya query lama tetap berfungsi tanpa diubah satu per satu.
        self.is_aktif = (self.status == 'aktif')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.kode} — {self.judul}'


CAKUPAN_KE_SASARAN_AUDITEE = {
    'prodi': ['AU-1'],
    'fakultas': ['AU-2'],
    # AU-3 (Unit/Biro/Lembaga) tidak punya model/role sendiri di sistem ini --
    # dilebur ke cakupan universitas (lihat plan sasaran_auditee non-Prodi).
    'universitas': ['AU-3', 'AU-4'],
}


def butir_untuk_cakupan(queryset, cakupan):
    """Filter ButirPenilaian berdasarkan sasaran_auditee yang relevan untuk
    satu cakupan Pengisian (prodi/fakultas/universitas)."""
    kode_list = CAKUPAN_KE_SASARAN_AUDITEE.get(cakupan, [])
    return queryset.filter(sasaran_auditee__overlap=kode_list)
