-- =====================================================================
-- SI-AMI UNISAN — DATABASE SETUP SCRIPT
-- File: 01_setup_schema.sql
-- Versi: 1.0
-- Tanggal: April 2026
-- Tujuan: Setup awal schema 'ami' di unisan_db dengan extensions, 
--         permissions, dan struktur dasar yang kompatibel PostgreSQL 14+
-- =====================================================================

-- ======================================================================
-- BAGIAN 1: PERSIAPAN DATABASE
-- ======================================================================
-- CATATAN: Jalankan sebagai superuser (postgres) terlebih dahulu
-- Asumsi: database 'unisan_db' sudah ada (tempat schema sso, sikd, pmb berada)

-- 1.1 Periksa database aktif (harus 'unisan_db')
SELECT current_database();

-- 1.2 Buat schema 'ami' jika belum ada
CREATE SCHEMA IF NOT EXISTS ami;

-- 1.3 Set search path agar schema 'ami' jadi default
-- (ini hanya untuk session ini; di production set di Django settings)
SET search_path TO ami, public;

-- 1.4 Tambahkan komentar pada schema
COMMENT ON SCHEMA ami IS 'Schema untuk Sistem Audit Mutu Internal (SI-AMI) UNISAN — bagian dari Sistem Informasi Terpadu Universitas Ichsan Gorontalo';


-- ======================================================================
-- BAGIAN 2: EXTENSIONS YANG DIBUTUHKAN
-- ======================================================================

-- 2.1 UUID untuk primary key beberapa tabel khusus (audit log, dokumen)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2.2 Untuk pencarian teks fulltext (Modul Pengarsipan)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 2.3 Untuk indexing GIN pada kolom JSONB
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Verifikasi extensions terpasang
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin');


-- ======================================================================
-- BAGIAN 3: ROLE & PERMISSION SETUP
-- ======================================================================
-- Buat role aplikasi yang akan dipakai Django untuk koneksi
-- Role ini terpisah dari 'postgres' superuser untuk keamanan

-- 3.1 Buat role aplikasi (skip jika sudah ada)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ami_user') THEN
        -- Role sudah ada (dibuat manual sebelumnya dengan password dari .env)
        RAISE NOTICE 'Role ami_user sudah ada — skip pembuatan, lanjut ke GRANT permissions';
    ELSE
        -- Fallback: jika role belum ada, buat dengan password placeholder
        -- WAJIB diganti via ALTER ROLE setelah ini!
        CREATE ROLE ami_user WITH LOGIN PASSWORD 'CHANGE_ME_AFTER_CREATION';
        RAISE NOTICE 'Role ami_user dibuat dengan password sementara — WAJIB ganti dengan ALTER ROLE!';
    END IF;
    
    -- Comment selalu di-update (aman walau role baru atau lama)
    COMMENT ON ROLE ami_user IS 'Role aplikasi Django SI-AMI — koneksi dari /var/www/ami';
END
$$;

-- 3.2 Berikan akses ke schema ami (full read/write/execute)
GRANT USAGE, CREATE ON SCHEMA ami TO ami_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ami TO ami_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ami TO ami_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ami TO ami_user;

-- 3.3 Default privileges untuk tabel/sequence yang dibuat di masa depan
ALTER DEFAULT PRIVILEGES IN SCHEMA ami 
    GRANT ALL ON TABLES TO ami_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ami 
    GRANT ALL ON SEQUENCES TO ami_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ami 
    GRANT EXECUTE ON FUNCTIONS TO ami_user;

-- 3.4 Berikan akses READ-ONLY ke schema lain untuk cross-schema FK
-- (akan dibuka ketika schema lain sudah tersedia)
DO $$
BEGIN
    -- Schema 'sso' (jika sudah ada)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'sso') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA sso TO ami_user';
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA sso TO ami_user';
        RAISE NOTICE 'Permission ke schema sso diberikan ke ami_user';
    ELSE
        RAISE NOTICE 'Schema sso belum ada — skip permission';
    END IF;
    
    -- Schema 'sikd' (jika sudah ada)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'sikd') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA sikd TO ami_user';
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA sikd TO ami_user';
        RAISE NOTICE 'Permission ke schema sikd diberikan ke ami_user';
    ELSE
        RAISE NOTICE 'Schema sikd belum ada — skip permission';
    END IF;
    
    -- Schema 'pmb' (jika sudah ada)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'pmb') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA pmb TO ami_user';
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA pmb TO ami_user';
        RAISE NOTICE 'Permission ke schema pmb diberikan ke ami_user';
    ELSE
        RAISE NOTICE 'Schema pmb belum ada — skip permission';
    END IF;
    
    -- Schema 'akademik' (akan jadi nanti)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'akademik') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA akademik TO ami_user';
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA akademik TO ami_user';
        RAISE NOTICE 'Permission ke schema akademik diberikan ke ami_user';
    ELSE
        RAISE NOTICE 'Schema akademik belum ada — gunakan tabel master internal di ami';
    END IF;
END
$$;


-- ======================================================================
-- BAGIAN 4: HELPER FUNCTIONS
-- ======================================================================

-- 4.1 Function: Update timestamp 'updated_at' otomatis
-- Akan dipakai sebagai trigger di setiap tabel yang punya kolom updated_at
CREATE OR REPLACE FUNCTION ami.fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION ami.fn_update_timestamp IS 'Auto-update kolom updated_at setiap kali row di-update';


-- 4.2 Function: Audit trail logger
-- Setiap perubahan di tabel kritis (penilaian DE, temuan, dll) dicatat
CREATE OR REPLACE FUNCTION ami.fn_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_action VARCHAR(10);
    v_old_data JSONB;
    v_new_data JSONB;
    v_user_id INTEGER;
BEGIN
    -- Tentukan jenis aksi
    IF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE';
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'INSERT' THEN
        v_action := 'INSERT';
        v_old_data := NULL;
        v_new_data := to_jsonb(NEW);
    END IF;
    
    -- Ambil user_id dari session (akan di-set Django via SET LOCAL)
    -- Default 0 jika tidak ada (system action)
    BEGIN
        v_user_id := current_setting('ami.current_user_id', true)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        v_user_id := 0;
    END;
    
    -- Insert ke tabel audit_log
    INSERT INTO ami.audit_log (
        table_name, record_id, action, 
        old_data, new_data, 
        changed_by, changed_at
    ) VALUES (
        TG_TABLE_NAME, 
        COALESCE(NEW.id, OLD.id),
        v_action, 
        v_old_data, 
        v_new_data,
        v_user_id, 
        NOW()
    );
    
    -- Return appropriate row
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION ami.fn_audit_trigger IS 'Mencatat semua perubahan data ke tabel audit_log untuk traceability';


-- ======================================================================
-- BAGIAN 5: TABEL AUDIT_LOG (FOUNDATION)
-- ======================================================================
-- Tabel ini dibuat duluan karena dirujuk oleh trigger semua tabel lain

CREATE TABLE IF NOT EXISTS ami.audit_log (
    id              BIGSERIAL PRIMARY KEY,
    table_name      VARCHAR(64) NOT NULL,
    record_id       BIGINT NOT NULL,
    action          VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data        JSONB,
    new_data        JSONB,
    changed_by      INTEGER NOT NULL DEFAULT 0,  -- FK ke sso.users (logical)
    changed_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address      INET,
    user_agent      TEXT
);

COMMENT ON TABLE ami.audit_log IS 'Audit trail semua perubahan data kritis di SI-AMI';

-- Index untuk pencarian audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record 
    ON ami.audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at 
    ON ami.audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by 
    ON ami.audit_log(changed_by);


-- ======================================================================
-- VERIFIKASI SETUP
-- ======================================================================

-- Pastikan semuanya OK
SELECT 
    'Schema ami' AS object_type, 
    EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'ami') AS exists;

SELECT 
    'Role ami_user' AS object_type, 
    EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'ami_user') AS exists;

SELECT 
    'Function fn_update_timestamp' AS object_type,
    EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'fn_update_timestamp' 
           AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'ami')) AS exists;

SELECT 
    'Function fn_audit_trigger' AS object_type,
    EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'fn_audit_trigger' 
           AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'ami')) AS exists;

SELECT 
    'Table audit_log' AS object_type,
    EXISTS(SELECT 1 FROM information_schema.tables 
           WHERE table_schema = 'ami' AND table_name = 'audit_log') AS exists;


-- ======================================================================
-- CATATAN UNTUK TIM DEVELOPER
-- ======================================================================
/*
LANGKAH SETELAH MENJALANKAN SCRIPT INI:

1. GANTI PASSWORD ami_user:
   ALTER ROLE ami_user WITH PASSWORD 'password_kuat_di_production';
   
2. SIMPAN PASSWORD DI .env DJANGO (JANGAN COMMIT KE GIT):
   DB_NAME=unisan_db
   DB_USER=ami_user
   DB_PASSWORD=password_kuat_di_production
   DB_HOST=localhost
   DB_PORT=5432
   DB_SCHEMA=ami

3. KONFIGURASI DJANGO settings.py:
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': env('DB_NAME'),
           'USER': env('DB_USER'),
           'PASSWORD': env('DB_PASSWORD'),
           'HOST': env('DB_HOST'),
           'PORT': env('DB_PORT'),
           'OPTIONS': {
               'options': '-c search_path=ami,public'
           }
       }
   }

4. UNTUK MENGAKSES DATA SCHEMA LAIN (sso, sikd, pmb):
   - Buat 'unmanaged' Django models dengan Meta.managed = False
   - Set Meta.db_table = 'sso\".\"users' (perhatikan escape quote)

5. JIKA PASTI VERSI POSTGRES BERAPA (15 atau 16):
   - Versi 15+: Bisa pakai MERGE statement (lebih cepat dari UPSERT)
   - Versi 16+: Bisa pakai logical replication untuk sync data ke arsip
   - Saya akan optimize script ini setelah tahu versi pasti
*/
