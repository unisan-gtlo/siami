# 📘 PANDUAN INSTALASI DATABASE SI-AMI UNISAN

**Deliverable #1: Database Schema**  
**Versi: 1.0**  
**Tanggal: April 2026**  
**Untuk: Tim Developer SI Terpadu UNISAN**

---

## 🎯 RINGKASAN

Anda akan menginstal **25 tabel** di schema `ami` yang menjadi fondasi Sistem Audit Mutu Internal UNISAN. Database ini dirancang untuk:

- ✅ Kompatibel **PostgreSQL 14, 15, dan 16**
- ✅ Multi-schema dengan **cross-schema FK** ke `sso`, `sikd`, `pmb`, `akademik`
- ✅ **Audit trail** otomatis untuk semua aksi kritis
- ✅ Sinkronisasi ke **arsip.unisan-g.id**
- ✅ **Optimal performance** dengan 50+ index strategis

**Estimasi waktu instalasi: 30-45 menit** (termasuk verifikasi)

---

## 📋 PRASYARAT

Sebelum mulai, pastikan tim sudah:

| Item | Cara Cek | Status |
|------|----------|--------|
| **PostgreSQL terinstal** | `psql --version` | Min. v14 |
| **Database `unisan_db` ada** | `psql -l` | Sudah ada |
| **User `postgres` access** | `sudo -u postgres psql` | Bisa login |
| **Schema lain ada** (sso, sikd, pmb) | `\dn` di psql | Tidak wajib, tapi recommended |
| **VPS punya disk space** | `df -h /var/lib/postgresql` | Min. 5 GB free |

### 🔍 Cek Versi PostgreSQL Anda

```bash
# Login SSH ke VPS UNISAN dulu:
ssh user@101.50.2.14

# Lalu jalankan salah satu:
psql --version
# Output contoh: psql (PostgreSQL) 15.4

# Atau lebih detail:
sudo -u postgres psql -c "SELECT version();"
```

**Kirim screenshot output ke saya jika ada concern tentang versi.**

---

## 📂 STRUKTUR FILE YANG ANDA TERIMA

Anda mendapat **3 file SQL** + **1 panduan ini**:

```
si_ami_dev/01_database/
├── 01_setup_schema.sql          ← Setup awal (schema, role, function)
├── 02_tables_master.sql         ← 11 tabel master + self-assessment
├── 03_tables_de_visitasi.sql    ← 14 tabel DE, visitasi, temuan, RTM
└── PANDUAN_INSTALASI.md         ← File ini
```

**Total: 25 tabel + 4 functions + 50+ index + 25+ trigger**

---

## 🚀 LANGKAH INSTALASI (URUT!)

### Langkah 1: Backup Database (WAJIB!)

```bash
# Backup unisan_db sebelum apapun
sudo -u postgres pg_dump unisan_db > /backup/unisan_db_pre_ami_$(date +%Y%m%d_%H%M).sql

# Verifikasi backup
ls -lh /backup/unisan_db_pre_ami_*.sql
```

### Langkah 2: Login ke Database

```bash
# Sebagai postgres superuser
sudo -u postgres psql unisan_db

# Anda akan masuk ke prompt:
# unisan_db=#
```

### Langkah 3: Jalankan File 1 (Setup Schema)

```bash
# Di dalam psql:
\i /path/to/si_ami_dev/01_database/01_setup_schema.sql

# Output yang diharapkan:
# CREATE SCHEMA
# CREATE EXTENSION
# CREATE ROLE  (atau NOTICE jika sudah ada)
# GRANT
# CREATE FUNCTION
# CREATE TABLE (audit_log)
# CREATE INDEX
# 
# Verifikasi: 
#  object_type | exists 
# -------------+--------
#  Schema ami  | t
#  Role ami_app| t
#  ... semua harus 't' (true)
```

### Langkah 4: Ganti Password Role

```sql
-- Di psql, GANTI password ami_app:
ALTER ROLE ami_app WITH PASSWORD 'PasswordKuat_UNISAN_2026!';

-- Catat password ini di tempat aman (.env Django nanti)
```

### Langkah 5: Jalankan File 2 (Tabel Master)

```bash
\i /path/to/si_ami_dev/01_database/02_tables_master.sql

# Output yang diharapkan:
# CREATE TABLE  (banyak)
# CREATE INDEX  (banyak)
# CREATE TRIGGER (banyak)
# INSERT 0 8    ← Sample data siklus 1-8
# INSERT 0 3    ← Sample data tahap
# INSERT 0 9    ← Sample data standar
#
# Verifikasi:
#         info        | jumlah 
# --------------------+--------
#  Total tabel ami:   |     11
```

### Langkah 6: Jalankan File 3 (DE, Visitasi, dll)

```bash
\i /path/to/si_ami_dev/01_database/03_tables_de_visitasi.sql

# Verifikasi akhir:
#         info        | jumlah 
# --------------------+--------
#  Total tabel ami:   |     25
```

### Langkah 7: Verifikasi Lengkap

```sql
-- Cek semua 25 tabel ada
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'ami' 
ORDER BY table_name;

-- Cek sample data
SELECT no_siklus, nama, status, is_current 
FROM ami.siklus ORDER BY no_siklus;

-- Cek 9 standar
SELECT kode, nama_pendek, no_urut FROM ami.standar ORDER BY no_urut;

-- Cek role ami_app punya akses
\du ami_app
```

---

## ✅ CHECKLIST KEBERHASILAN

Setelah instalasi, pastikan SEMUA ini berhasil:

- [ ] Schema `ami` ada (`\dn` melihat ami)
- [ ] **25 tabel** terbuat di schema ami
- [ ] **3 extensions** aktif (uuid-ossp, pg_trgm, btree_gin)
- [ ] **Role `ami_app`** ada dan punya password baru
- [ ] **2 functions** ada (`fn_update_timestamp`, `fn_audit_trigger`)
- [ ] **Sample data**: 8 siklus, 3 tahap, 9 standar
- [ ] **Audit log** kosong tapi ready (`SELECT COUNT(*) FROM ami.audit_log`)
- [ ] **Trigger updated_at** aktif (test: update 1 row, lihat updated_at berubah)
- [ ] **Cross-schema permission** diberikan (jika sso/sikd/pmb sudah ada)

---

## 🧪 TES SEDERHANA SETELAH INSTALASI

Jalankan test ini untuk memastikan database benar-benar berfungsi:

```sql
-- 1. Tes insert fakultas
INSERT INTO ami.fakultas (kode, nama, nama_singkat, source_id) 
VALUES ('FE', 'Fakultas Ekonomi', 'FE', 1);

-- 2. Tes insert prodi
INSERT INTO ami.prodi (
    fakultas_id, kode, kode_pddikti, nama, strata
) VALUES (
    1, 'MNJ-S1', '61201', 'S1 Manajemen', 'S1'
);

-- 3. Tes auto-update timestamp (jeda 2 detik dulu)
UPDATE ami.prodi SET nama = 'S1 Manajemen (test)' WHERE id = 1;

SELECT id, nama, created_at, updated_at, 
       updated_at > created_at AS timestamp_terupdate 
FROM ami.prodi;

-- 4. Tes pengisian
INSERT INTO ami.pengisian (siklus_id, prodi_id, status, total_butir)
VALUES (8, 1, 'sedang_diisi', 62);

-- 5. Cek pengisian dengan persentase progress otomatis
SELECT id, status, total_butir, butir_terisi, persentase_progress 
FROM ami.pengisian;

-- 6. Cleanup test data
DELETE FROM ami.pengisian;
DELETE FROM ami.prodi WHERE kode = 'MNJ-S1';
DELETE FROM ami.fakultas WHERE kode = 'FE';

-- 7. Cek audit log mencatat aksi tadi (jika ada trigger di tabel ini)
SELECT COUNT(*) FROM ami.audit_log;
```

**Jika SEMUA test di atas sukses → Database SIAP digunakan! ✅**

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "permission denied for schema sso/sikd/pmb"

**Penyebab**: Role `ami_app` belum punya akses ke schema lain.

**Solusi**:
```sql
-- Sebagai postgres superuser:
GRANT USAGE ON SCHEMA sso TO ami_app;
GRANT SELECT ON ALL TABLES IN SCHEMA sso TO ami_app;

-- Ulangi untuk sikd, pmb, akademik
```

### ❌ Error: "extension pg_trgm does not exist"

**Penyebab**: Extension belum diinstal di OS level.

**Solusi**:
```bash
# Untuk Rocky Linux:
sudo dnf install postgresql15-contrib

# Restart PostgreSQL
sudo systemctl restart postgresql-15

# Lalu coba lagi:
sudo -u postgres psql unisan_db -c "CREATE EXTENSION pg_trgm;"
```

### ❌ Error: "must be owner of table" saat ALTER

**Penyebab**: Bukan superuser yang menjalankan.

**Solusi**:
```bash
# Selalu pakai sudo -u postgres atau login sebagai postgres
sudo -u postgres psql unisan_db
```

### ❌ Error: "duplicate key value violates unique constraint"

**Penyebab**: Sample data sudah pernah diinsert.

**Solusi**: Aman diabaikan — sudah ada `ON CONFLICT DO NOTHING`. Atau:
```sql
-- Jika mau reset dan mulai ulang:
TRUNCATE ami.siklus, ami.tahap, ami.standar CASCADE;
-- Lalu jalankan lagi file 02_tables_master.sql
```

---

## 🔐 KONFIGURASI DJANGO (LANGKAH BERIKUTNYA)

Setelah database siap, di Django settings.py:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'unisan_db',
        'USER': 'ami_app',
        'PASSWORD': 'PasswordKuat_UNISAN_2026!',  # dari .env
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=ami,public'  # Default ke schema ami
        }
    }
}
```

**File `.env` (jangan commit ke git!)**:
```env
DB_NAME=unisan_db
DB_USER=ami_app
DB_PASSWORD=PasswordKuat_UNISAN_2026!
DB_HOST=localhost
DB_PORT=5432
DB_SCHEMA=ami
```

---

## 📊 STRUKTUR DATABASE LENGKAP

### Kelompok 1: Master Data (4 tabel)
1. `ami.fakultas` — mirror dari schema akademik
2. `ami.prodi` — master prodi UNISAN
3. `ami.user_ami` — user dengan role AMI
4. `ami.dosen_cache` — cache data dosen dari SIKD

### Kelompok 2: Domain Siklus (4 tabel)
5. `ami.siklus` — Siklus 1-8 AMI
6. `ami.tahap` — 3 tahap pelaksanaan
7. `ami.standar` — 9 Standar SN-Dikti
8. `ami.butir_penilaian` — 62 butir per siklus

### Kelompok 3: Self-Assessment (3 tabel)
9. `ami.pengisian` — header self-assessment
10. `ami.jawaban_butir` — detail jawaban auditee
11. `ami.dokumen_bukti` — repository bukti

### Kelompok 4: Desk Evaluasi (3 tabel) ⭐
12. `ami.de_penugasan` — SK auditor DE
13. `ami.de_penilaian` — skor 1/0 + PLOR ⭐ JANTUNG SISTEM
14. `ami.de_daftar_tilik` — daftar tilik untuk visitasi

### Kelompok 5: Visitasi (3 tabel)
15. `ami.visitasi` — header visitasi
16. `ami.visitasi_anggota` — tim auditor
17. `ami.visitasi_agenda` — sesi-sesi visitasi

### Kelompok 6: Temuan & Tindak Lanjut (3 tabel)
18. `ami.temuan` — KTB/KTS/OB/BP
19. `ami.fvtb` — Form Verifikasi Tindak Lanjut
20. `ami.fvtb_progress_log` — log update

### Kelompok 7: RTM (3 tabel)
21. `ami.rtm` — header rapat
22. `ami.rtm_agenda` — agenda keputusan strategis
23. `ami.rtm_notulen` — chat real-time

### Kelompok 8: Audit & Pengarsipan (2 tabel)
24. `ami.audit_log` — semua audit trail
25. `ami.arsip_metadata` — metadata pengarsipan
26. `ami.notifikasi` — sistem notifikasi

---

## 🎯 LANGKAH SELANJUTNYA

Setelah database terinstal:

1. ✅ **Konfirmasi ke saya**: berhasil/error/butuh klarifikasi
2. ⏭️ **Saya kirim Deliverable #2**: API REST Specification (~60 endpoints)
3. ⏭️ Tim mulai siapkan Django project skeleton
4. ⏭️ Cek mekanisme SSO (sso.unisan-g.id) bersama-sama

---

## 📞 SUPPORT

Jika ada error/pertanyaan saat instalasi:
1. Screenshot error message lengkap
2. Sebutkan: file mana, langkah ke berapa, versi PostgreSQL
3. Saya bantu fix segera

**Mari kita bangun SI-AMI UNISAN bersama-sama! 🚀**

---

*Dokumen ini akan diperbarui jika ada penyesuaian.*  
*— Generated for LP3M UNISAN, April 2026*
