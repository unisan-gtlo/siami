from django.contrib import admin

from .models import DokumenBukti, JawabanButir, Pengisian


class JawabanButirInline(admin.TabularInline):
    model = JawabanButir
    extra = 0
    fields = ('butir', 'is_terisi', 'is_locked', 'nilai_kuantitatif', 'nilai_pilihan')
    autocomplete_fields = ('butir',)


@admin.register(Pengisian)
class PengisianAdmin(admin.ModelAdmin):
    list_display = (
        'prodi', 'siklus', 'status', 'butir_terisi', 'total_butir',
        'persentase_progress', 'submitted_at',
    )
    list_filter = ('siklus', 'status')
    search_fields = ('prodi__nama', 'prodi__kode')
    autocomplete_fields = ('siklus', 'prodi', 'operator', 'upm_validator')
    inlines = [JawabanButirInline]


@admin.register(JawabanButir)
class JawabanButirAdmin(admin.ModelAdmin):
    list_display = ('pengisian', 'butir', 'is_terisi', 'is_locked', 'memenuhi_iku', 'sumber_data')
    list_filter = ('is_terisi', 'is_locked', 'sumber_data', 'memenuhi_iku')
    search_fields = ('pengisian__prodi__nama', 'butir__kode', 'butir__judul')
    autocomplete_fields = ('pengisian', 'butir', 'diisi_oleh')


@admin.register(DokumenBukti)
class DokumenBuktiAdmin(admin.ModelAdmin):
    list_display = ('nama_dokumen', 'pengisian', 'jenis_sumber', 'status', 'diunggah_pada')
    list_filter = ('jenis_sumber', 'status')
    search_fields = ('nama_dokumen', 'pengisian__prodi__nama')
    autocomplete_fields = ('pengisian', 'butir', 'jawaban', 'diverifikasi_oleh', 'diunggah_oleh')
