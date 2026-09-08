from django.contrib import admin

from .models import Fakultas, Prodi


@admin.register(Fakultas)
class FakultasAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'nama_singkat', 'is_aktif', 'updated_at')
    list_filter = ('is_aktif',)
    search_fields = ('kode', 'nama', 'nama_singkat')
    ordering = ('nama',)


@admin.register(Prodi)
class ProdiAdmin(admin.ModelAdmin):
    list_display = (
        'kode', 'nama', 'fakultas', 'strata',
        'akreditasi_peringkat', 'status_akreditasi', 'is_aktif',
    )
    list_filter = ('strata', 'fakultas', 'is_aktif', 'akreditasi_peringkat', 'status_akreditasi')
    search_fields = ('kode', 'kode_pddikti', 'nama')
    ordering = ('nama',)
    autocomplete_fields = ('fakultas',)
