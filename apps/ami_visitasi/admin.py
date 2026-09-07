from django.contrib import admin

from .models import Visitasi, VisitasiAgenda, VisitasiAnggota


class VisitasiAnggotaInline(admin.TabularInline):
    model = VisitasiAnggota
    extra = 0
    fields = ('user', 'role', 'is_hadir')
    autocomplete_fields = ('user',)


class VisitasiAgendaInline(admin.TabularInline):
    model = VisitasiAgenda
    extra = 0
    fields = ('no_urut', 'waktu_mulai', 'waktu_selesai', 'judul_sesi', 'status', 'pic')
    autocomplete_fields = ('pic',)


@admin.register(Visitasi)
class VisitasiAdmin(admin.ModelAdmin):
    list_display = (
        'pengisian', 'tgl_visitasi', 'ketua_tim', 'konfirmasi_status', 'status',
    )
    list_filter = ('siklus', 'status', 'konfirmasi_status')
    search_fields = ('pengisian__prodi__nama', 'sk_no')
    autocomplete_fields = ('siklus', 'pengisian', 'ketua_tim', 'notulis')
    inlines = [VisitasiAnggotaInline, VisitasiAgendaInline]
