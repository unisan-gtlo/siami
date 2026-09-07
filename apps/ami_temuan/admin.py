from django.contrib import admin

from .models import Fvtb, FvtbProgressLog, Temuan


class FvtbProgressLogInline(admin.TabularInline):
    model = FvtbProgressLog
    extra = 0
    fields = ('progress_sebelum', 'progress_sesudah', 'update_text', 'diupdate_oleh', 'diupdate_pada')
    readonly_fields = ('diupdate_pada',)
    autocomplete_fields = ('diupdate_oleh',)


@admin.register(Temuan)
class TemuanAdmin(admin.ModelAdmin):
    list_display = (
        'no_temuan', 'judul', 'pengisian', 'klasifikasi', 'sumber_temuan',
        'status', 'urgensi', 'tenggat_tindak_lanjut',
    )
    list_filter = ('siklus', 'klasifikasi', 'sumber_temuan', 'status', 'urgensi', 'layak_replikasi')
    search_fields = ('no_temuan', 'judul', 'pengisian__prodi__nama')
    autocomplete_fields = (
        'siklus', 'pengisian', 'butir', 'de_penilaian', 'visitasi', 'dilaporkan_oleh',
    )


@admin.register(Fvtb)
class FvtbAdmin(admin.ModelAdmin):
    list_display = (
        'no_fvtb', 'temuan', 'pic', 'progress_persen', 'status', 'tenggat_selesai',
        'sudah_diverifikasi',
    )
    list_filter = ('status', 'sudah_diverifikasi')
    search_fields = ('no_fvtb', 'temuan__no_temuan', 'temuan__judul')
    autocomplete_fields = ('temuan', 'pic', 'verifikator')
    inlines = [FvtbProgressLogInline]
