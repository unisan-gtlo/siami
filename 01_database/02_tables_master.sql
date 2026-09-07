-- =====================================================================
-- SI-AMI UNISAN — TABEL MASTER & DOMAIN INTI
-- File: 02_tables_master.sql
-- Versi: 1.0
-- Total Tabel: 15 tabel master + domain siklus AMI + self-assessment
-- =====================================================================

SET search_path TO ami, public;

-- ======================================================================
-- ====== KELOMPOK 1: MASTER DATA (mirror dari schema lain) =============
-- ======================================================================
-- Tabel-tabel ini menjadi "lokal cache" dari schema lain agar:
-- 1. Cross-schema FK bisa dilakukan tanpa lock antar-schema
-- 2. Performa query JOIN lebih cepat
-- 3. Sistem AMI tetap bisa jalan jika schema lain down sementara
-- 4. Data master di-sync nightly via Django management command

-- ----------------------------------------------------------------------
-- TABEL 1: ami.fakultas (mirror dari akademik.fakultas)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.fakultas (
    id              SERIAL PRIMARY KEY,
    kode            VARCHAR(20) UNIQUE NOT NULL,
    nama            VARCHAR(150) NOT NULL,
    nama_singkat    VARCHAR(20) NOT NULL,
    dekan_user_id   INTEGER,                          -- Logical FK ke sso.users
    upm_user_id     INTEGER,                          -- Ketua UPM Fakultas
    alamat          TEXT,
    telp            VARCHAR(20),
    email           VARCHAR(100),
    is_aktif        BOOLEAN DEFAULT TRUE,
    
    -- Sync metadata
    source_schema   VARCHAR(20) DEFAULT 'akademik',
    source_id       INTEGER,                          -- ID di schema asal
    last_synced_at  TIMESTAMP,
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.fakultas IS 'Master data fakultas — mirror dari schema akademik, di-sync nightly';

CREATE INDEX idx_fakultas_kode ON ami.fakultas(kode);
CREATE INDEX idx_fakultas_aktif ON ami.fakultas(is_aktif);

-- Trigger untuk update timestamp
CREATE TRIGGER trg_fakultas_update 
    BEFORE UPDATE ON ami.fakultas 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 2: ami.prodi (mirror dari akademik.prodi)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.prodi (
    id              SERIAL PRIMARY KEY,
    fakultas_id     INTEGER NOT NULL REFERENCES ami.fakultas(id),
    kode            VARCHAR(20) UNIQUE NOT NULL,      -- Kode internal UNISAN
    kode_pddikti    VARCHAR(20) UNIQUE,               -- Kode PD-Dikti (e.g. 61201)
    nama            VARCHAR(200) NOT NULL,
    nama_inggris    VARCHAR(200),
    strata          VARCHAR(10) NOT NULL CHECK (strata IN ('D3', 'D4', 'S1', 'S2', 'S3', 'Profesi')),
    
    -- Pengelola
    kaprodi_user_id     INTEGER,                      -- FK ke sso.users
    sekprodi_user_id    INTEGER,
    
    -- SK Pendirian
    sk_pendirian_no     VARCHAR(100),
    sk_pendirian_tgl    DATE,
    sk_pendirian_file   VARCHAR(500),                 -- Path file PDF
    
    -- Akreditasi terkini
    akreditasi_lembaga  VARCHAR(20) CHECK (akreditasi_lembaga IN ('BAN-PT', 'LAM-PTKes', 'LAMSAMA', 'LAMINFOKOM', 'LAM-Teknik', 'Belum')),
    akreditasi_peringkat VARCHAR(20) CHECK (akreditasi_peringkat IN ('Unggul', 'Baik Sekali', 'Baik', 'Terakreditasi', 'Belum')),
    akreditasi_no_sk    VARCHAR(100),
    akreditasi_tgl_sk   DATE,
    akreditasi_berlaku_sd DATE,
    
    -- Status
    is_aktif        BOOLEAN DEFAULT TRUE,
    
    -- Sync metadata  
    source_schema   VARCHAR(20) DEFAULT 'akademik',
    source_id       INTEGER,
    last_synced_at  TIMESTAMP,
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.prodi IS 'Master data program studi — sumber utama auditee dalam AMI';

CREATE INDEX idx_prodi_fakultas ON ami.prodi(fakultas_id);
CREATE INDEX idx_prodi_kode_pddikti ON ami.prodi(kode_pddikti);
CREATE INDEX idx_prodi_strata ON ami.prodi(strata);

CREATE TRIGGER trg_prodi_update 
    BEFORE UPDATE ON ami.prodi 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 3: ami.user_ami (mirror SSO + role assignment AMI)
-- ----------------------------------------------------------------------
-- Tabel ini menyimpan user yang aktif di AMI dengan role-nya
-- Profile dasar tetap di sso.users, di sini hanya role + extension

CREATE TABLE IF NOT EXISTS ami.user_ami (
    id                  SERIAL PRIMARY KEY,
    sso_user_id         INTEGER UNIQUE NOT NULL,      -- FK logical ke sso.users
    nidn_nip            VARCHAR(30) UNIQUE,
    nama_lengkap        VARCHAR(200) NOT NULL,        -- Cache dari sso untuk tampilan cepat
    email               VARCHAR(150) NOT NULL,        -- Cache
    foto_url            VARCHAR(500),                 -- Cache
    
    -- Affiliation
    fakultas_id         INTEGER REFERENCES ami.fakultas(id),
    prodi_id            INTEGER REFERENCES ami.prodi(id),
    
    -- Role di AMI (multi-role possible, disimpan via tabel user_role)
    -- Field di sini hanya untuk filter cepat
    is_auditor_de       BOOLEAN DEFAULT FALSE,
    is_auditor_visitasi BOOLEAN DEFAULT FALSE,
    is_upm              BOOLEAN DEFAULT FALSE,
    is_lp3m             BOOLEAN DEFAULT FALSE,
    is_pimpinan         BOOLEAN DEFAULT FALSE,
    
    -- Auditor specific
    sertifikasi_auditor VARCHAR(100),                 -- e.g. "CIIQA #2024-035"
    pengalaman_audit_thn INTEGER,
    pakta_integritas_signed_at TIMESTAMP,
    pakta_integritas_file VARCHAR(500),
    
    -- Status
    is_aktif        BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP,
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.user_ami IS 'User aktif di SI-AMI dengan ekstensi role spesifik AMI';

CREATE INDEX idx_user_ami_sso ON ami.user_ami(sso_user_id);
CREATE INDEX idx_user_ami_nidn ON ami.user_ami(nidn_nip);
CREATE INDEX idx_user_ami_fakultas ON ami.user_ami(fakultas_id);
CREATE INDEX idx_user_ami_auditor_de ON ami.user_ami(is_auditor_de) WHERE is_auditor_de = TRUE;
CREATE INDEX idx_user_ami_aktif ON ami.user_ami(is_aktif) WHERE is_aktif = TRUE;

CREATE TRIGGER trg_user_ami_update 
    BEFORE UPDATE ON ami.user_ami 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 4: ami.dosen_cache (cache data dosen dari schema sikd)
-- ----------------------------------------------------------------------
-- Untuk auto-link IKU butir SDM (Standar 4) tanpa lock ke schema sikd
CREATE TABLE IF NOT EXISTS ami.dosen_cache (
    id                  SERIAL PRIMARY KEY,
    sikd_dosen_id       INTEGER UNIQUE NOT NULL,      -- FK logical ke sikd.dosen
    nidn                VARCHAR(20) UNIQUE NOT NULL,
    nama_lengkap        VARCHAR(200) NOT NULL,
    prodi_id            INTEGER REFERENCES ami.prodi(id),
    
    -- Kualifikasi (untuk butir 4.1 SDM)
    pendidikan_terakhir VARCHAR(20) CHECK (pendidikan_terakhir IN ('S1', 'S2', 'S3', 'Profesi')),
    jabatan_fungsional  VARCHAR(50),                  -- Lektor, Asisten Ahli, dll
    sertifikasi_dosen   BOOLEAN DEFAULT FALSE,        -- Punya sertifikasi pendidik
    
    -- Status kepegawaian
    status_dosen        VARCHAR(20) CHECK (status_dosen IN ('PNS', 'NonPNS', 'Yayasan', 'Kontrak', 'Honorer')),
    is_dosen_tetap      BOOLEAN DEFAULT FALSE,
    is_aktif            BOOLEAN DEFAULT TRUE,
    
    -- Metadata sync
    last_synced_at      TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.dosen_cache IS 'Cache data dosen dari schema sikd untuk auto-link AMI Standar 4 SDM';

CREATE INDEX idx_dosen_cache_nidn ON ami.dosen_cache(nidn);
CREATE INDEX idx_dosen_cache_prodi ON ami.dosen_cache(prodi_id);
CREATE INDEX idx_dosen_cache_pendidikan ON ami.dosen_cache(pendidikan_terakhir);
CREATE INDEX idx_dosen_cache_tetap ON ami.dosen_cache(is_dosen_tetap) WHERE is_dosen_tetap = TRUE;

CREATE TRIGGER trg_dosen_cache_update 
    BEFORE UPDATE ON ami.dosen_cache 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ======================================================================
-- ====== KELOMPOK 2: DOMAIN SIKLUS AMI =================================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 5: ami.siklus (Daftar siklus AMI dari S1 sampai sekarang)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.siklus (
    id              SERIAL PRIMARY KEY,
    no_siklus       INTEGER UNIQUE NOT NULL,          -- 1, 2, 3, ..., 8
    nama            VARCHAR(50) NOT NULL,             -- "Siklus 8"
    tahun_akademik  VARCHAR(20) NOT NULL,             -- "2025/2026"
    
    -- Periode
    tgl_mulai       DATE NOT NULL,
    tgl_selesai     DATE NOT NULL,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'planning' 
                    CHECK (status IN ('planning', 'active', 'closed', 'archived')),
    is_current      BOOLEAN DEFAULT FALSE,            -- Hanya 1 yang TRUE
    
    -- Dokumen pendukung
    sk_rektor_no    VARCHAR(100),
    sk_rektor_tgl   DATE,
    sk_rektor_file  VARCHAR(500),
    
    -- Konfigurasi
    konfig          JSONB,                            -- Setting custom per siklus
    
    -- Closing info
    closing_date    DATE,
    closing_notulen_file VARCHAR(500),
    
    keterangan      TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.siklus IS 'Master data siklus AMI — UNISAN saat ini di Siklus 8 (2025/2026)';

CREATE UNIQUE INDEX idx_siklus_current 
    ON ami.siklus(is_current) WHERE is_current = TRUE;

CREATE TRIGGER trg_siklus_update 
    BEFORE UPDATE ON ami.siklus 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();

-- Insert sample data Siklus 1-8
INSERT INTO ami.siklus (no_siklus, nama, tahun_akademik, tgl_mulai, tgl_selesai, status, is_current) VALUES
    (1, 'Siklus 1', '2018/2019', '2018-04-01', '2018-10-30', 'archived', FALSE),
    (2, 'Siklus 2', '2019/2020', '2019-04-01', '2019-10-25', 'archived', FALSE),
    (3, 'Siklus 3', '2020/2021', '2020-04-01', '2020-10-18', 'archived', FALSE),
    (4, 'Siklus 4', '2021/2022', '2021-04-01', '2021-10-22', 'archived', FALSE),
    (5, 'Siklus 5', '2022/2023', '2022-04-01', '2022-10-28', 'archived', FALSE),
    (6, 'Siklus 6', '2023/2024', '2023-04-01', '2023-10-25', 'archived', FALSE),
    (7, 'Siklus 7', '2024/2025', '2024-04-01', '2024-10-30', 'closed', FALSE),
    (8, 'Siklus 8', '2025/2026', '2026-05-01', '2026-10-30', 'active', TRUE)
ON CONFLICT (no_siklus) DO NOTHING;


-- ----------------------------------------------------------------------
-- TABEL 6: ami.tahap (3 tahap pelaksanaan AMI)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.tahap (
    id              SERIAL PRIMARY KEY,
    kode            VARCHAR(20) UNIQUE NOT NULL,
    nama            VARCHAR(100) NOT NULL,
    no_urut         INTEGER NOT NULL,
    deskripsi       TEXT,
    durasi_hari     INTEGER,                          -- Estimasi durasi per tahap
    is_aktif        BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE ami.tahap IS '3 tahap pelaksanaan AMI: AMI Online, Desk Evaluasi, Visitasi Lapangan';

INSERT INTO ami.tahap (kode, nama, no_urut, deskripsi, durasi_hari) VALUES
    ('AMI_ONLINE', 'AMI Online (Self-Assessment)', 1, 'Auditee mengisi instrumen IKU-IKT secara mandiri di platform online', 30),
    ('DESK_EVAL', 'Desk Evaluasi (DE)', 2, 'Auditor menelaah dokumen secara online dan memberikan skor binary 1/0', 21),
    ('VISITASI', 'Visitasi Lapangan', 3, 'Auditor melakukan verifikasi langsung di prodi auditee', 14)
ON CONFLICT (kode) DO NOTHING;


-- ----------------------------------------------------------------------
-- TABEL 7: ami.standar (9 Standar SN-Dikti)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.standar (
    id              SERIAL PRIMARY KEY,
    kode            VARCHAR(10) UNIQUE NOT NULL,      -- "1", "2", ..., "9"
    nama            VARCHAR(100) NOT NULL,
    nama_pendek     VARCHAR(50) NOT NULL,             -- "VMTS", "Tata Pamong", dll
    deskripsi       TEXT,
    no_urut         INTEGER NOT NULL,
    warna_hex       VARCHAR(7) DEFAULT '#1B7BB8',     -- Warna untuk UI
    is_aktif        BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE ami.standar IS '9 Standar SN-Dikti yang menjadi acuan AMI';

INSERT INTO ami.standar (kode, nama, nama_pendek, no_urut, warna_hex) VALUES
    ('1', 'Visi, Misi, Tujuan, dan Strategi', 'VMTS', 1, '#0E5A8A'),
    ('2', 'Tata Pamong, Tata Kelola, dan Kerjasama', 'Tata Pamong', 2, '#1B7BB8'),
    ('3', 'Mahasiswa', 'Mahasiswa', 3, '#5BAEDB'),
    ('4', 'Sumber Daya Manusia', 'SDM', 4, '#27AE60'),
    ('5', 'Keuangan, Sarana, dan Prasarana', 'Sapras', 5, '#F2C94C'),
    ('6', 'Pendidikan', 'Pendidikan', 6, '#E0A800'),
    ('7', 'Penelitian', 'Penelitian', 7, '#E74C3C'),
    ('8', 'Pengabdian Kepada Masyarakat', 'PKM', 8, '#9B59B6'),
    ('9', 'Luaran dan Capaian Tridarma', 'Luaran', 9, '#2C3E50')
ON CONFLICT (kode) DO NOTHING;


-- ----------------------------------------------------------------------
-- TABEL 8: ami.butir_penilaian (62 butir per siklus)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.butir_penilaian (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    standar_id          INTEGER NOT NULL REFERENCES ami.standar(id),
    
    kode                VARCHAR(20) NOT NULL,         -- "3.1", "4.2", dll
    judul               VARCHAR(300) NOT NULL,
    deskripsi           TEXT,
    
    -- Metode penilaian
    jenis_input         VARCHAR(30) NOT NULL CHECK (jenis_input IN (
                            'numerik',       -- Input angka
                            'rasio',         -- Format X:Y
                            'persentase',    -- 0-100%
                            'pilihan',       -- Dropdown
                            'narasi',        -- Text panjang
                            'tabel_dinamis', -- Tabel multi-row
                            'auto_iku'       -- Auto-pull dari schema lain
                        )),
    
    -- Target IKU
    target_iku          NUMERIC(10,4),
    target_satuan       VARCHAR(50),                  -- "rasio", "%", "orang", dll
    operator_target     VARCHAR(5) CHECK (operator_target IN ('>=', '<=', '=', '>', '<')),
    
    -- Auto-fetch config (jika jenis_input = 'auto_iku')
    auto_source_schema  VARCHAR(20),                  -- 'sikd', 'pmb', 'akademik'
    auto_source_table   VARCHAR(50),
    auto_query_template TEXT,                         -- SQL template
    
    -- Bobot dan klasifikasi
    bobot               INTEGER DEFAULT 1,
    is_wajib            BOOLEAN DEFAULT TRUE,
    is_kuantitatif      BOOLEAN DEFAULT FALSE,
    
    -- Panduan & rujukan
    panduan_pengisian   TEXT,
    rujukan_dokumen     VARCHAR(500),                 -- Rujukan ke dokumen panduan
    rujukan_sn_dikti    VARCHAR(200),                 -- "SN-Dikti pasal X ayat Y"
    
    no_urut             INTEGER NOT NULL,
    is_aktif            BOOLEAN DEFAULT TRUE,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(siklus_id, kode)
);

COMMENT ON TABLE ami.butir_penilaian IS '62 butir penilaian per siklus AMI berdasarkan SN-Dikti';

CREATE INDEX idx_butir_siklus_standar ON ami.butir_penilaian(siklus_id, standar_id);
CREATE INDEX idx_butir_jenis ON ami.butir_penilaian(jenis_input);
CREATE INDEX idx_butir_auto ON ami.butir_penilaian(auto_source_schema) 
    WHERE auto_source_schema IS NOT NULL;

CREATE TRIGGER trg_butir_update 
    BEFORE UPDATE ON ami.butir_penilaian 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ======================================================================
-- ====== KELOMPOK 3: SELF-ASSESSMENT (AMI ONLINE) ======================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 9: ami.pengisian (Header self-assessment per prodi per siklus)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.pengisian (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    prodi_id            INTEGER NOT NULL REFERENCES ami.prodi(id),
    
    -- Status pengisian
    status              VARCHAR(30) NOT NULL DEFAULT 'belum_mulai' CHECK (status IN (
                            'belum_mulai',
                            'sedang_diisi',
                            'submit',           -- Auditee selesai isi
                            'validasi_upm',     -- UPM Fakultas validasi
                            'siap_de',          -- Siap untuk Desk Evaluasi
                            'completed'
                        )),
    
    -- Progress tracking
    total_butir         INTEGER DEFAULT 0,
    butir_terisi        INTEGER DEFAULT 0,
    persentase_progress NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE WHEN total_butir > 0 
             THEN ROUND(butir_terisi::NUMERIC / total_butir * 100, 2)
             ELSE 0 END
    ) STORED,
    
    -- Skor agregat (auto-calc dari butir terisi)
    skor_total          NUMERIC(8,2),
    skor_per_standar    JSONB,                        -- {"1": 85, "2": 78, ...}
    
    -- Operator
    operator_user_id    INTEGER REFERENCES ami.user_ami(id),
    upm_validator_id    INTEGER REFERENCES ami.user_ami(id),
    
    -- Timestamp tahapan
    started_at          TIMESTAMP,
    submitted_at        TIMESTAMP,
    validated_at        TIMESTAMP,
    
    -- Catatan
    catatan             TEXT,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(siklus_id, prodi_id)
);

COMMENT ON TABLE ami.pengisian IS 'Header self-assessment AMI per prodi per siklus';

CREATE INDEX idx_pengisian_status ON ami.pengisian(status);
CREATE INDEX idx_pengisian_prodi ON ami.pengisian(prodi_id);
CREATE INDEX idx_pengisian_siklus ON ami.pengisian(siklus_id);

CREATE TRIGGER trg_pengisian_update 
    BEFORE UPDATE ON ami.pengisian 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 10: ami.jawaban_butir (Detail jawaban per butir)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.jawaban_butir (
    id                  BIGSERIAL PRIMARY KEY,
    pengisian_id        INTEGER NOT NULL REFERENCES ami.pengisian(id) ON DELETE CASCADE,
    butir_id            INTEGER NOT NULL REFERENCES ami.butir_penilaian(id),
    
    -- Jawaban (multi-format menggunakan JSONB)
    nilai_kuantitatif   NUMERIC(15,4),                -- Untuk numerik/rasio/%
    nilai_pilihan       VARCHAR(200),                 -- Untuk dropdown
    nilai_narasi        TEXT,                         -- Untuk narasi
    nilai_tabel         JSONB,                        -- Untuk tabel dinamis
    nilai_auto          JSONB,                        -- Hasil auto-fetch dari schema lain
    
    -- Auto-calculation result
    rasio_hasil         NUMERIC(10,4),                -- Hasil hitungan rasio
    persentase_capaian  NUMERIC(5,2),                 -- % capaian terhadap target
    memenuhi_iku        BOOLEAN,                      -- Apakah memenuhi target IKU
    
    -- Metadata
    sumber_data         VARCHAR(30) DEFAULT 'manual' CHECK (sumber_data IN (
                            'manual',           -- Diketik auditee
                            'auto_pmb',         -- Auto dari SI PMB
                            'auto_sikd',        -- Auto dari SIKD
                            'auto_akademik',    -- Auto dari Akademik
                            'import_excel'      -- Dari upload excel
                        )),
    
    -- Catatan auditee
    catatan_auditee     TEXT,
    
    -- Status
    is_terisi           BOOLEAN DEFAULT FALSE,
    is_locked           BOOLEAN DEFAULT FALSE,        -- Tidak bisa diedit setelah submit
    
    -- Timestamps
    diisi_oleh_user_id  INTEGER REFERENCES ami.user_ami(id),
    diisi_pada          TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(pengisian_id, butir_id)
);

COMMENT ON TABLE ami.jawaban_butir IS 'Detail jawaban auditee untuk setiap butir penilaian';

CREATE INDEX idx_jawaban_pengisian ON ami.jawaban_butir(pengisian_id);
CREATE INDEX idx_jawaban_butir ON ami.jawaban_butir(butir_id);
CREATE INDEX idx_jawaban_terisi ON ami.jawaban_butir(is_terisi);
CREATE INDEX idx_jawaban_iku ON ami.jawaban_butir(memenuhi_iku);

-- GIN index untuk pencarian dalam JSONB
CREATE INDEX idx_jawaban_nilai_tabel_gin ON ami.jawaban_butir USING GIN (nilai_tabel);

CREATE TRIGGER trg_jawaban_update 
    BEFORE UPDATE ON ami.jawaban_butir 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();

-- Audit trigger untuk traceability
CREATE TRIGGER trg_jawaban_audit 
    AFTER INSERT OR UPDATE OR DELETE ON ami.jawaban_butir 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_audit_trigger();


-- ----------------------------------------------------------------------
-- TABEL 11: ami.dokumen_bukti (Repository link dan file bukti)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.dokumen_bukti (
    id                  BIGSERIAL PRIMARY KEY,
    pengisian_id        INTEGER NOT NULL REFERENCES ami.pengisian(id) ON DELETE CASCADE,
    butir_id            INTEGER REFERENCES ami.butir_penilaian(id),
    jawaban_id          BIGINT REFERENCES ami.jawaban_butir(id),
    
    -- Identifikasi dokumen
    nama_dokumen        VARCHAR(300) NOT NULL,
    deskripsi           TEXT,
    
    -- Sumber dokumen
    jenis_sumber        VARCHAR(20) NOT NULL CHECK (jenis_sumber IN (
                            'upload_file',      -- File diupload langsung
                            'link_drive',       -- Link Google Drive
                            'link_url',         -- Link URL umum
                            'auto_api',         -- Auto-fetched via API
                            'cross_schema'      -- Dari schema lain (sikd, pmb, dll)
                        )),
    
    -- Detail per jenis sumber
    file_path           VARCHAR(500),                 -- Untuk upload_file
    file_size_bytes     BIGINT,
    file_mime_type      VARCHAR(100),
    
    link_url            TEXT,                         -- Untuk link_drive/link_url
    link_terverifikasi  BOOLEAN DEFAULT FALSE,        -- Apakah link masih aktif
    link_last_checked   TIMESTAMP,
    
    api_endpoint        VARCHAR(500),                 -- Untuk auto_api
    cross_schema_ref    JSONB,                        -- Untuk cross_schema
    
    -- Format
    format              VARCHAR(20),                  -- "PDF", "Excel", "Word", dll
    
    -- Status verifikasi
    status              VARCHAR(30) DEFAULT 'belum_diverifikasi' CHECK (status IN (
                            'belum_diverifikasi',
                            'menunggu_upm',
                            'terverifikasi',
                            'ditolak',
                            'perlu_revisi'
                        )),
    catatan_verifikasi  TEXT,
    diverifikasi_oleh   INTEGER REFERENCES ami.user_ami(id),
    diverifikasi_pada   TIMESTAMP,
    
    -- Upload metadata
    diunggah_oleh       INTEGER REFERENCES ami.user_ami(id),
    diunggah_pada       TIMESTAMP DEFAULT NOW(),
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.dokumen_bukti IS 'Repository dokumen bukti pendukung AMI - file upload, link, atau cross-schema';

CREATE INDEX idx_dokumen_pengisian ON ami.dokumen_bukti(pengisian_id);
CREATE INDEX idx_dokumen_butir ON ami.dokumen_bukti(butir_id);
CREATE INDEX idx_dokumen_status ON ami.dokumen_bukti(status);
CREATE INDEX idx_dokumen_jenis ON ami.dokumen_bukti(jenis_sumber);

CREATE TRIGGER trg_dokumen_update 
    BEFORE UPDATE ON ami.dokumen_bukti 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ======================================================================
-- VERIFIKASI HASIL
-- ======================================================================

-- Hitung tabel yang berhasil dibuat
SELECT 
    'Total tabel ami:' AS info,
    COUNT(*) AS jumlah
FROM information_schema.tables 
WHERE table_schema = 'ami';

-- Daftar tabel
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = 'ami' AND table_name = t.table_name) AS jml_kolom
FROM information_schema.tables t
WHERE table_schema = 'ami' 
ORDER BY table_name;
