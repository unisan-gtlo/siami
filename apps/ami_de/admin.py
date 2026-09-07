from django.contrib import admin

from .models import DeDaftarTilik, DePenilaian, DePenugasan


class DePenilaianInline(admin.TabularInline):
    model = DePenilaian
    extra = 0
    fields = ('butir', 'skor', 'klasifikasi', 'is_finalisasi')
    autocomplete_fields = ('butir',)


@admin.register(DePenugasan)
class DePenugasanAdmin(admin.ModelAdmin):
    list_display = (
        'pengisian', 'auditor', 'role_dalam_tim', 'status',
        'butir_dinilai', 'total_butir', 'tenggat_de',
    )
    list_filter = ('siklus', 'status', 'role_dalam_tim')
    search_fields = ('pengisian__prodi__nama', 'auditor__user__username', 'sk_no')
    autocomplete_fields = ('siklus', 'pengisian', 'auditor')
    inlines = [DePenilaianInline]


@admin.register(DePenilaian)
class DePenilaianAdmin(admin.ModelAdmin):
    list_display = (
        'penugasan', 'butir', 'skor', 'klasifikasi',
        'is_draft', 'is_finalisasi', 'dinilai_pada',
    )
    list_filter = ('skor', 'klasifikasi', 'is_draft', 'is_finalisasi')
    search_fields = ('penugasan__pengisian__prodi__nama', 'butir__kode', 'butir__judul')
    autocomplete_fields = ('penugasan', 'butir', 'jawaban')


@admin.register(DeDaftarTilik)
class DeDaftarTilikAdmin(admin.ModelAdmin):
    list_display = (
        'penugasan', 'butir', 'prioritas', 'metode_verifikasi', 'status_visitasi',
    )
    list_filter = ('prioritas', 'metode_verifikasi', 'status_visitasi')
    search_fields = ('deskripsi_tilik', 'penugasan__pengisian__prodi__nama')
    autocomplete_fields = ('penugasan', 'butir', 'penilaian', 'diperiksa_oleh')
