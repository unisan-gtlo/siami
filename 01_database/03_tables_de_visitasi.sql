-- =====================================================================
-- SI-AMI UNISAN — TABEL DESK EVALUASI, VISITASI, TEMUAN, RTM
-- File: 03_tables_de_visitasi.sql
-- Versi: 1.0
-- Total Tabel: 14 tabel (jantung sistem AMI)
-- =====================================================================

SET search_path TO ami, public;

-- ======================================================================
-- ====== KELOMPOK 4: DESK EVALUASI (DE) — JANTUNG SISTEM ==============
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 12: ami.de_penugasan (SK Penugasan Auditor DE)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.de_penugasan (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    pengisian_id        INTEGER NOT NULL REFERENCES ami.pengisian(id),  -- Auditee
    
    -- Auditor (1 prodi bisa punya 2-3 auditor untuk cross-check)
    auditor_user_id     INTEGER NOT NULL REFERENCES ami.user_ami(id),
    role_dalam_tim      VARCHAR(20) DEFAULT 'auditor' CHECK (role_dalam_tim IN (
                            'ketua_tim', 'auditor', 'pendamping'
                        )),
    
    -- SK Penugasan
    sk_no               VARCHAR(100) NOT NULL,        -- "SK Rektor No. 042/AMI/2026"
    sk_tgl              DATE NOT NULL,
    sk_file             VARCHAR(500),
    
    -- Periode pelaksanaan
    tgl_mulai_de        DATE NOT NULL,
    tenggat_de          DATE NOT NULL,
    tgl_selesai_aktual  DATE,
    
    -- Status
    status              VARCHAR(30) DEFAULT 'ditugaskan' CHECK (status IN (
                            'ditugaskan',
                            'dimulai',
                            'on_progress',
                            'selesai_de',
                            'difinalisasi',
                            'dibatalkan'
                        )),
    
    -- Progress
    total_butir         INTEGER DEFAULT 0,
    butir_dinilai       INTEGER DEFAULT 0,
    butir_skor_1        INTEGER DEFAULT 0,
    butir_skor_0        INTEGER DEFAULT 0,
    
    -- Konflik kepentingan check
    konflik_kepentingan_signed BOOLEAN DEFAULT FALSE,
    konflik_kepentingan_signed_at TIMESTAMP,
    
    -- Catatan
    catatan_lp3m        TEXT,
    catatan_auditor     TEXT,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    -- 1 auditor tidak boleh punya penugasan ganda untuk prodi yang sama
    UNIQUE(pengisian_id, auditor_user_id)
);

COMMENT ON TABLE ami.de_penugasan IS 'Penugasan auditor DE per prodi per siklus — 1 prodi bisa multiple auditor';

CREATE INDEX idx_de_penugasan_siklus ON ami.de_penugasan(siklus_id);
CREATE INDEX idx_de_penugasan_auditor ON ami.de_penugasan(auditor_user_id);
CREATE INDEX idx_de_penugasan_status ON ami.de_penugasan(status);
CREATE INDEX idx_de_penugasan_tenggat ON ami.de_penugasan(tenggat_de) 
    WHERE status NOT IN ('selesai_de', 'difinalisasi', 'dibatalkan');

CREATE TRIGGER trg_de_penugasan_update 
    BEFORE UPDATE ON ami.de_penugasan 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 13: ami.de_penilaian (Penilaian per butir oleh auditor) ⭐ KRITIS
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.de_penilaian (
    id                  BIGSERIAL PRIMARY KEY,
    penugasan_id        INTEGER NOT NULL REFERENCES ami.de_penugasan(id) ON DELETE CASCADE,
    butir_id            INTEGER NOT NULL REFERENCES ami.butir_penilaian(id),
    jawaban_id          BIGINT REFERENCES ami.jawaban_butir(id),  -- Link ke jawaban auditee
    
    -- ⭐ SKOR BINARY (Inti DE)
    skor                INTEGER CHECK (skor IN (0, 1)),  -- 1=sesuai, 0=tidak sesuai
    
    -- Klasifikasi (jika skor 0 atau khusus BP)
    klasifikasi         VARCHAR(10) CHECK (klasifikasi IN (
                            'KTB',  -- Ketidaksesuaian Berat
                            'KTS',  -- Ketidaksesuaian Sedang
                            'OB',   -- Observasi
                            'BP'    -- Best Practice
                        )),
    
    -- ⭐ FRAMEWORK PLOR (Problem-Location-Objective-Reference)
    plor_problem        TEXT,                         -- P: Apa masalahnya
    plor_location       VARCHAR(300),                 -- L: Di mana terjadi
    plor_objective      VARCHAR(500),                 -- O: Standar yang dilanggar
    plor_reference      VARCHAR(500),                 -- R: Bukti dokumen
    
    -- Catatan tambahan
    catatan_auditor     TEXT,
    rekomendasi_visitasi TEXT,                        -- Apa yang harus diverifikasi visitasi
    
    -- Verifikasi dokumen oleh auditor
    dokumen_diperiksa   JSONB,                        -- Array dokumen_id yang diperiksa
    
    -- Status
    is_draft            BOOLEAN DEFAULT TRUE,
    is_finalisasi       BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    dinilai_pada        TIMESTAMP,
    difinalisasi_pada   TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(penugasan_id, butir_id)
);

COMMENT ON TABLE ami.de_penilaian IS 'Penilaian Desk Evaluasi per butir — skor binary 1/0 + framework PLOR';
COMMENT ON COLUMN ami.de_penilaian.skor IS 'Skor binary: 1=sesuai standar, 0=tidak sesuai (lihat klasifikasi)';

CREATE INDEX idx_de_penilaian_penugasan ON ami.de_penilaian(penugasan_id);
CREATE INDEX idx_de_penilaian_butir ON ami.de_penilaian(butir_id);
CREATE INDEX idx_de_penilaian_skor ON ami.de_penilaian(skor);
CREATE INDEX idx_de_penilaian_klasifikasi ON ami.de_penilaian(klasifikasi);
CREATE INDEX idx_de_penilaian_finalisasi ON ami.de_penilaian(is_finalisasi);

CREATE TRIGGER trg_de_penilaian_update 
    BEFORE UPDATE ON ami.de_penilaian 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();

-- Audit trigger (KRITIS untuk DE — semua aksi auditor harus tercatat)
CREATE TRIGGER trg_de_penilaian_audit 
    AFTER INSERT OR UPDATE OR DELETE ON ami.de_penilaian 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_audit_trigger();


-- ----------------------------------------------------------------------
-- TABEL 14: ami.de_daftar_tilik (Daftar Tilik untuk Visitasi)
-- ----------------------------------------------------------------------
-- Output dari DE — apa yang harus diverifikasi auditor visitasi
CREATE TABLE IF NOT EXISTS ami.de_daftar_tilik (
    id                  BIGSERIAL PRIMARY KEY,
    penugasan_id        INTEGER NOT NULL REFERENCES ami.de_penugasan(id) ON DELETE CASCADE,
    butir_id            INTEGER NOT NULL REFERENCES ami.butir_penilaian(id),
    penilaian_id        BIGINT REFERENCES ami.de_penilaian(id),
    
    -- Item tilik
    deskripsi_tilik     TEXT NOT NULL,
    prioritas           VARCHAR(10) CHECK (prioritas IN ('tinggi', 'sedang', 'rendah')),
    metode_verifikasi   VARCHAR(30) CHECK (metode_verifikasi IN (
                            'wawancara', 'observasi', 'review_dokumen', 
                            'fgd', 'inspeksi_lapangan'
                        )),
    
    -- Sasaran wawancara (jika metode wawancara)
    sasaran_pic         VARCHAR(200),                 -- "Ka. Prodi", "Mahasiswa angkatan 2023"
    
    -- Status verifikasi (diisi saat visitasi)
    status_visitasi     VARCHAR(20) DEFAULT 'belum_diperiksa' CHECK (status_visitasi IN (
                            'belum_diperiksa',
                            'terkonfirmasi',
                            'tidak_terkonfirmasi',
                            'perlu_followup'
                        )),
    catatan_visitasi    TEXT,
    diperiksa_oleh      INTEGER REFERENCES ami.user_ami(id),
    diperiksa_pada      TIMESTAMP,
    
    no_urut             INTEGER,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.de_daftar_tilik IS 'Daftar tilik output DE — sebagai panduan auditor visitasi';

CREATE INDEX idx_tilik_penugasan ON ami.de_daftar_tilik(penugasan_id);
CREATE INDEX idx_tilik_status ON ami.de_daftar_tilik(status_visitasi);

CREATE TRIGGER trg_tilik_update 
    BEFORE UPDATE ON ami.de_daftar_tilik 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ======================================================================
-- ====== KELOMPOK 5: VISITASI LAPANGAN ================================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 15: ami.visitasi (Header visitasi per prodi)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.visitasi (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    pengisian_id        INTEGER NOT NULL REFERENCES ami.pengisian(id),
    
    -- Jadwal
    tgl_visitasi        DATE NOT NULL,
    waktu_mulai         TIME,
    waktu_selesai       TIME,
    tempat              VARCHAR(300),
    
    -- Tim auditor (header — detail di tabel visitasi_anggota)
    ketua_tim_user_id   INTEGER REFERENCES ami.user_ami(id),
    notulis_user_id     INTEGER REFERENCES ami.user_ami(id),
    
    -- SK Tim
    sk_no               VARCHAR(100),
    sk_tgl              DATE,
    sk_file             VARCHAR(500),
    
    -- Konfirmasi auditee
    konfirmasi_status   VARCHAR(20) DEFAULT 'belum_konfirmasi' CHECK (konfirmasi_status IN (
                            'belum_konfirmasi', 'dikonfirmasi', 'minta_reschedule', 'ditolak'
                        )),
    konfirmasi_pada     TIMESTAMP,
    
    -- Status pelaksanaan
    status              VARCHAR(30) DEFAULT 'terjadwal' CHECK (status IN (
                            'terjadwal',
                            'dimulai',
                            'on_progress',
                            'selesai',
                            'closing_done',
                            'dibatalkan'
                        )),
    
    -- Output
    ba_opening_file     VARCHAR(500),                 -- Berita acara opening
    ba_closing_file     VARCHAR(500),                 -- Berita acara closing
    sertifikat_file     VARCHAR(500),                 -- Sertifikat AMI
    
    -- Closing info
    tgl_closing         DATE,
    catatan_closing     TEXT,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(siklus_id, pengisian_id)
);

COMMENT ON TABLE ami.visitasi IS 'Header pelaksanaan visitasi lapangan per prodi';

CREATE INDEX idx_visitasi_siklus ON ami.visitasi(siklus_id);
CREATE INDEX idx_visitasi_tgl ON ami.visitasi(tgl_visitasi);
CREATE INDEX idx_visitasi_status ON ami.visitasi(status);

CREATE TRIGGER trg_visitasi_update 
    BEFORE UPDATE ON ami.visitasi 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 16: ami.visitasi_anggota (Anggota tim visitasi)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.visitasi_anggota (
    id                  SERIAL PRIMARY KEY,
    visitasi_id         INTEGER NOT NULL REFERENCES ami.visitasi(id) ON DELETE CASCADE,
    user_id             INTEGER NOT NULL REFERENCES ami.user_ami(id),
    
    role                VARCHAR(20) NOT NULL CHECK (role IN (
                            'ketua_tim', 'anggota', 'notulis', 'pendamping_lp3m'
                        )),
    
    -- Konflik kepentingan
    konflik_kepentingan TEXT,                         -- Catatan jika ada
    
    -- Kehadiran
    is_hadir            BOOLEAN DEFAULT FALSE,
    waktu_hadir         TIMESTAMP,
    waktu_pulang        TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(visitasi_id, user_id)
);

COMMENT ON TABLE ami.visitasi_anggota IS 'Anggota tim visitasi lapangan';

CREATE INDEX idx_visitasi_anggota_user ON ami.visitasi_anggota(user_id);


-- ----------------------------------------------------------------------
-- TABEL 17: ami.visitasi_agenda (Sesi-sesi dalam visitasi)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.visitasi_agenda (
    id                  SERIAL PRIMARY KEY,
    visitasi_id         INTEGER NOT NULL REFERENCES ami.visitasi(id) ON DELETE CASCADE,
    
    no_urut             INTEGER NOT NULL,
    waktu_mulai         TIME NOT NULL,
    waktu_selesai       TIME NOT NULL,
    judul_sesi          VARCHAR(200) NOT NULL,
    deskripsi           TEXT,
    pic_user_id         INTEGER REFERENCES ami.user_ami(id),
    
    -- Status sesi
    status              VARCHAR(20) DEFAULT 'belum_mulai' CHECK (status IN (
                            'belum_mulai', 'sedang_berlangsung', 'selesai', 'dilewati'
                        )),
    
    -- Hasil sesi
    notulen_sesi        TEXT,
    foto_dokumentasi    JSONB,                        -- Array URL foto
    
    started_at          TIMESTAMP,
    ended_at            TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.visitasi_agenda IS 'Sesi/agenda dalam pelaksanaan visitasi (opening, wawancara, observasi, FGD, closing)';

CREATE INDEX idx_agenda_visitasi ON ami.visitasi_agenda(visitasi_id, no_urut);


-- ======================================================================
-- ====== KELOMPOK 6: TEMUAN, PTK, DAN TINDAK LANJUT ===================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 18: ami.temuan (Konsolidasi temuan dari DE + Visitasi)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.temuan (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    pengisian_id        INTEGER NOT NULL REFERENCES ami.pengisian(id),
    butir_id            INTEGER REFERENCES ami.butir_penilaian(id),
    
    -- Sumber temuan
    sumber_temuan       VARCHAR(20) NOT NULL CHECK (sumber_temuan IN (
                            'de', 'visitasi', 'manual'
                        )),
    de_penilaian_id     BIGINT REFERENCES ami.de_penilaian(id),
    visitasi_id         INTEGER REFERENCES ami.visitasi(id),
    
    -- Klasifikasi
    klasifikasi         VARCHAR(10) NOT NULL CHECK (klasifikasi IN ('KTB', 'KTS', 'OB', 'BP')),
    no_temuan           VARCHAR(50),                  -- Auto-generated: "T-S8-001"
    
    -- Detail PLOR
    judul               VARCHAR(300) NOT NULL,
    deskripsi_problem   TEXT NOT NULL,
    lokasi_temuan       VARCHAR(300),
    standar_dilanggar   VARCHAR(500),
    bukti_referensi     TEXT,
    
    -- Dampak dan urgensi
    dampak              TEXT,
    urgensi             VARCHAR(10) CHECK (urgensi IN ('rendah', 'sedang', 'tinggi', 'kritis')),
    
    -- Tenggat tindak lanjut (otomatis berdasar klasifikasi)
    tenggat_tindak_lanjut DATE,                       -- KTB: 30 hari, KTS: 60 hari, OB: 90 hari
    
    -- Status
    status              VARCHAR(30) DEFAULT 'baru' CHECK (status IN (
                            'baru',
                            'diidentifikasi',
                            'rencana_tindak_lanjut',
                            'sedang_tindak_lanjut',
                            'verifikasi',
                            'closed',
                            'eskalasi'
                        )),
    
    -- Best practice (jika klasifikasi = BP)
    layak_replikasi     BOOLEAN DEFAULT FALSE,
    knowledge_base_id   INTEGER,                      -- FK ke tabel knowledge base nanti
    
    -- Auditor pelapor
    dilaporkan_oleh     INTEGER REFERENCES ami.user_ami(id),
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.temuan IS 'Temuan AMI - konsolidasi dari DE dan Visitasi - klasifikasi KTB/KTS/OB/BP';

CREATE INDEX idx_temuan_siklus ON ami.temuan(siklus_id);
CREATE INDEX idx_temuan_klasifikasi ON ami.temuan(klasifikasi);
CREATE INDEX idx_temuan_status ON ami.temuan(status);
CREATE INDEX idx_temuan_tenggat ON ami.temuan(tenggat_tindak_lanjut)
    WHERE status NOT IN ('closed');
CREATE INDEX idx_temuan_bp ON ami.temuan(layak_replikasi) WHERE layak_replikasi = TRUE;

CREATE TRIGGER trg_temuan_update 
    BEFORE UPDATE ON ami.temuan 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();

CREATE TRIGGER trg_temuan_audit 
    AFTER INSERT OR UPDATE OR DELETE ON ami.temuan 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_audit_trigger();


-- ----------------------------------------------------------------------
-- TABEL 19: ami.fvtb (Form Verifikasi Tindak Lanjut)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.fvtb (
    id                  SERIAL PRIMARY KEY,
    temuan_id           INTEGER NOT NULL REFERENCES ami.temuan(id),
    no_fvtb             VARCHAR(50) UNIQUE,           -- Auto: "FVTB-2026-001"
    
    -- PDCA — PLAN
    rencana_tindakan    TEXT NOT NULL,
    pic_user_id         INTEGER REFERENCES ami.user_ami(id),
    pic_unit            VARCHAR(200),                 -- "Ka. Prodi", "WR I", dll
    target_capaian      TEXT,
    estimasi_anggaran   NUMERIC(15,2),
    sumber_anggaran     VARCHAR(200),
    
    -- PDCA — DO (progress execution)
    progress_persen     INTEGER DEFAULT 0 CHECK (progress_persen BETWEEN 0 AND 100),
    update_terakhir     TEXT,
    update_pada         TIMESTAMP,
    
    -- Tenggat
    tgl_mulai           DATE,
    tenggat_selesai     DATE NOT NULL,
    tgl_selesai_aktual  DATE,
    
    -- PDCA — CHECK (verifikasi)
    sudah_diverifikasi  BOOLEAN DEFAULT FALSE,
    verifikator_user_id INTEGER REFERENCES ami.user_ami(id),
    catatan_verifikasi  TEXT,
    bukti_verifikasi    JSONB,                        -- Array dokumen bukti
    diverifikasi_pada   TIMESTAMP,
    
    -- PDCA — ACT (standardization)
    standarisasi_dilakukan BOOLEAN DEFAULT FALSE,
    catatan_standarisasi   TEXT,
    
    -- Status keseluruhan
    status              VARCHAR(20) DEFAULT 'plan' CHECK (status IN (
                            'plan', 'do', 'check', 'act', 'closed', 'eskalasi'
                        )),
    
    -- Notifikasi
    last_notifikasi_sent TIMESTAMP,                   -- Untuk auto-reminder
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.fvtb IS 'Form Verifikasi Tindak Lanjut - tracking PDCA per temuan';

CREATE INDEX idx_fvtb_temuan ON ami.fvtb(temuan_id);
CREATE INDEX idx_fvtb_status ON ami.fvtb(status);
CREATE INDEX idx_fvtb_tenggat ON ami.fvtb(tenggat_selesai) WHERE status != 'closed';
CREATE INDEX idx_fvtb_pic ON ami.fvtb(pic_user_id);

CREATE TRIGGER trg_fvtb_update 
    BEFORE UPDATE ON ami.fvtb 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 20: ami.fvtb_progress_log (Log progress F-VTB per update)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.fvtb_progress_log (
    id                  BIGSERIAL PRIMARY KEY,
    fvtb_id             INTEGER NOT NULL REFERENCES ami.fvtb(id) ON DELETE CASCADE,
    
    progress_sebelum    INTEGER,
    progress_sesudah    INTEGER,
    update_text         TEXT NOT NULL,
    bukti_url           VARCHAR(500),
    
    diupdate_oleh       INTEGER REFERENCES ami.user_ami(id),
    diupdate_pada       TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.fvtb_progress_log IS 'Log perubahan progress F-VTB untuk traceability tindak lanjut';

CREATE INDEX idx_fvtb_log_fvtb ON ami.fvtb_progress_log(fvtb_id);


-- ======================================================================
-- ====== KELOMPOK 7: RAPAT TINJAUAN MANAJEMEN (RTM) ===================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 21: ami.rtm (Header Rapat Tinjauan Manajemen)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.rtm (
    id                  SERIAL PRIMARY KEY,
    siklus_id           INTEGER NOT NULL REFERENCES ami.siklus(id),
    
    judul               VARCHAR(300) NOT NULL,
    tgl_rapat           DATE NOT NULL,
    waktu_mulai         TIME,
    waktu_selesai       TIME,
    tempat              VARCHAR(300),
    
    -- Status
    status              VARCHAR(20) DEFAULT 'terjadwal' CHECK (status IN (
                            'terjadwal', 'sedang_berlangsung', 'selesai', 'dibatalkan'
                        )),
    
    -- Pemimpin rapat
    pemimpin_user_id    INTEGER REFERENCES ami.user_ami(id),
    notulis_user_id     INTEGER REFERENCES ami.user_ami(id),
    
    -- Output
    notulen_file        VARCHAR(500),
    sk_keputusan_file   VARCHAR(500),
    foto_dokumentasi    JSONB,
    
    -- Statistik (cache)
    jml_peserta         INTEGER DEFAULT 0,
    jml_keputusan       INTEGER DEFAULT 0,
    jml_action_item     INTEGER DEFAULT 0,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.rtm IS 'Rapat Tinjauan Manajemen pasca-AMI per siklus';

CREATE INDEX idx_rtm_siklus ON ami.rtm(siklus_id);
CREATE INDEX idx_rtm_status ON ami.rtm(status);

CREATE TRIGGER trg_rtm_update 
    BEFORE UPDATE ON ami.rtm 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 22: ami.rtm_agenda (Agenda keputusan strategis)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.rtm_agenda (
    id                  SERIAL PRIMARY KEY,
    rtm_id              INTEGER NOT NULL REFERENCES ami.rtm(id) ON DELETE CASCADE,
    
    no_urut             INTEGER NOT NULL,
    judul               VARCHAR(300) NOT NULL,
    deskripsi           TEXT,
    
    prioritas           VARCHAR(20) CHECK (prioritas IN ('rendah', 'sedang', 'tinggi', 'kritis')),
    
    -- Estimasi anggaran
    estimasi_anggaran   NUMERIC(15,2),
    sumber_anggaran     VARCHAR(200),
    
    -- PIC dan target
    pic_user_id         INTEGER REFERENCES ami.user_ami(id),
    pic_unit            VARCHAR(200),
    target_completion   DATE,
    
    -- Voting (jika voting digital)
    is_voting_enabled   BOOLEAN DEFAULT FALSE,
    voting_setuju       INTEGER DEFAULT 0,
    voting_tidak        INTEGER DEFAULT 0,
    voting_abstain      INTEGER DEFAULT 0,
    
    -- Status keputusan
    keputusan           VARCHAR(20) CHECK (keputusan IN (
                            'pending', 'disetujui', 'ditolak', 'ditunda'
                        )),
    keputusan_pada      TIMESTAMP,
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.rtm_agenda IS 'Agenda keputusan strategis dalam RTM';

CREATE INDEX idx_rtm_agenda_rtm ON ami.rtm_agenda(rtm_id);


-- ----------------------------------------------------------------------
-- TABEL 23: ami.rtm_notulen (Real-time collaborative chat)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.rtm_notulen (
    id                  BIGSERIAL PRIMARY KEY,
    rtm_id              INTEGER NOT NULL REFERENCES ami.rtm(id) ON DELETE CASCADE,
    
    user_id             INTEGER NOT NULL REFERENCES ami.user_ami(id),
    isi                 TEXT NOT NULL,
    
    -- Tipe pesan
    tipe                VARCHAR(20) DEFAULT 'komentar' CHECK (tipe IN (
                            'komentar', 'pertanyaan', 'usulan', 
                            'action_item', 'keputusan', 'sistem'
                        )),
    
    -- Action item extracted
    is_action_item      BOOLEAN DEFAULT FALSE,
    action_pic_user_id  INTEGER REFERENCES ami.user_ami(id),
    action_deadline     DATE,
    action_status       VARCHAR(20) CHECK (action_status IN (
                            'open', 'in_progress', 'done', 'cancelled'
                        )),
    
    -- Metadata
    waktu_kirim         TIMESTAMP DEFAULT NOW(),
    edited              BOOLEAN DEFAULT FALSE,
    edited_at           TIMESTAMP,
    
    -- Reply thread
    reply_to_id         BIGINT REFERENCES ami.rtm_notulen(id)
);

COMMENT ON TABLE ami.rtm_notulen IS 'Notulen RTM real-time collaborative (chat-style)';

CREATE INDEX idx_rtm_notulen_rtm ON ami.rtm_notulen(rtm_id, waktu_kirim);
CREATE INDEX idx_rtm_notulen_action ON ami.rtm_notulen(is_action_item) 
    WHERE is_action_item = TRUE;


-- ======================================================================
-- ====== KELOMPOK 8: PENGARSIPAN ======================================
-- ======================================================================

-- ----------------------------------------------------------------------
-- TABEL 24: ami.arsip_metadata (Metadata pengarsipan lintas siklus)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.arsip_metadata (
    id                  BIGSERIAL PRIMARY KEY,
    
    -- Identifikasi dokumen
    siklus_id           INTEGER REFERENCES ami.siklus(id),
    prodi_id            INTEGER REFERENCES ami.prodi(id),
    kategori            VARCHAR(50) NOT NULL CHECK (kategori IN (
                            'form_penilaian', 'temuan_ptk', 'best_practice',
                            'sk_rektor', 'notulen_rtm', 'sertifikat_ami',
                            'berita_acara', 'laporan_lengkap', 'lainnya'
                        )),
    
    -- File details
    nama_dokumen        VARCHAR(300) NOT NULL,
    deskripsi           TEXT,
    file_path           VARCHAR(500) NOT NULL,
    file_size_bytes     BIGINT,
    file_mime_type      VARCHAR(100),
    file_hash_sha256    VARCHAR(64),                  -- Untuk integritas
    
    -- Indeksasi untuk pencarian
    tags                TEXT[],                       -- Array tag
    fulltext_content    TEXT,                         -- Konten extracted untuk fulltext search
    fulltext_search     TSVECTOR,                     -- Auto-generated by trigger
    
    -- Sinkronisasi ke arsip.unisan-g.id
    synced_to_arsip     BOOLEAN DEFAULT FALSE,
    arsip_universitas_id VARCHAR(100),                -- ID di sistem arsip pusat
    synced_at           TIMESTAMP,
    
    -- Retensi
    retensi_sd_tahun    INTEGER,                      -- Disimpan sampai tahun berapa
    is_permanen         BOOLEAN DEFAULT FALSE,
    
    -- Akses
    is_publik           BOOLEAN DEFAULT FALSE,
    akses_role          TEXT[],                       -- Array role yang boleh akses
    
    -- Metadata
    diunggah_oleh       INTEGER REFERENCES ami.user_ami(id),
    diunggah_pada       TIMESTAMP DEFAULT NOW(),
    
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.arsip_metadata IS 'Metadata arsip dokumen AMI lintas siklus + sync ke arsip.unisan-g.id';

-- Index untuk pencarian
CREATE INDEX idx_arsip_siklus ON ami.arsip_metadata(siklus_id);
CREATE INDEX idx_arsip_prodi ON ami.arsip_metadata(prodi_id);
CREATE INDEX idx_arsip_kategori ON ami.arsip_metadata(kategori);
CREATE INDEX idx_arsip_tags ON ami.arsip_metadata USING GIN(tags);
CREATE INDEX idx_arsip_fulltext ON ami.arsip_metadata USING GIN(fulltext_search);
CREATE INDEX idx_arsip_synced ON ami.arsip_metadata(synced_to_arsip);

-- Trigger untuk auto-update fulltext_search
CREATE OR REPLACE FUNCTION ami.fn_update_arsip_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fulltext_search := to_tsvector('indonesian', 
        COALESCE(NEW.nama_dokumen, '') || ' ' ||
        COALESCE(NEW.deskripsi, '') || ' ' ||
        COALESCE(NEW.fulltext_content, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_arsip_search 
    BEFORE INSERT OR UPDATE ON ami.arsip_metadata 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_arsip_search();

CREATE TRIGGER trg_arsip_update 
    BEFORE UPDATE ON ami.arsip_metadata 
    FOR EACH ROW EXECUTE FUNCTION ami.fn_update_timestamp();


-- ----------------------------------------------------------------------
-- TABEL 25: ami.notifikasi (Sistem notifikasi internal)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ami.notifikasi (
    id                  BIGSERIAL PRIMARY KEY,
    
    -- Penerima
    to_user_id          INTEGER NOT NULL REFERENCES ami.user_ami(id),
    
    -- Konten
    judul               VARCHAR(300) NOT NULL,
    isi                 TEXT,
    tipe                VARCHAR(30) CHECK (tipe IN (
                            'info', 'reminder', 'tenggat', 'eskalasi', 
                            'persetujuan', 'penugasan_baru', 'sistem'
                        )),
    
    -- Reference ke entitas terkait
    ref_entity          VARCHAR(50),                  -- "temuan", "fvtb", "penugasan_de", dll
    ref_entity_id       BIGINT,
    ref_url             VARCHAR(500),                 -- Link untuk action
    
    -- Channel pengiriman
    channel_email       BOOLEAN DEFAULT FALSE,
    channel_wa          BOOLEAN DEFAULT FALSE,
    channel_inapp       BOOLEAN DEFAULT TRUE,
    
    -- Status
    is_read             BOOLEAN DEFAULT FALSE,
    read_at             TIMESTAMP,
    is_sent_email       BOOLEAN DEFAULT FALSE,
    is_sent_wa          BOOLEAN DEFAULT FALSE,
    
    -- Priority
    priority            VARCHAR(10) DEFAULT 'normal' CHECK (priority IN (
                            'low', 'normal', 'high', 'urgent'
                        )),
    
    created_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE ami.notifikasi IS 'Notifikasi internal SI-AMI - in-app, email, WhatsApp';

CREATE INDEX idx_notif_user ON ami.notifikasi(to_user_id, is_read);
CREATE INDEX idx_notif_unread ON ami.notifikasi(to_user_id) WHERE is_read = FALSE;


-- ======================================================================
-- VERIFIKASI HASIL AKHIR
-- ======================================================================

SELECT 
    'Total tabel ami:' AS info,
    COUNT(*) AS jumlah
FROM information_schema.tables 
WHERE table_schema = 'ami';

-- Daftar lengkap dengan jumlah kolom dan index
SELECT 
    t.table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = 'ami' AND table_name = t.table_name) AS jml_kolom,
    (SELECT COUNT(*) FROM pg_indexes 
     WHERE schemaname = 'ami' AND tablename = t.table_name) AS jml_index
FROM information_schema.tables t
WHERE table_schema = 'ami' 
ORDER BY t.table_name;

-- Total records di tabel master (sample data)
SELECT 'siklus' AS tabel, COUNT(*) AS records FROM ami.siklus
UNION ALL SELECT 'tahap', COUNT(*) FROM ami.tahap
UNION ALL SELECT 'standar', COUNT(*) FROM ami.standar;
