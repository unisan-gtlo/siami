from django.contrib import admin

from .models import ButirPenilaian, Siklus, Standar, Tahap


@admin.register(Siklus)
class SiklusAdmin(admin.ModelAdmin):
    list_display = ('no_siklus', 'nama', 'tahun_akademik', 'status', 'is_current')
    list_filter = ('status', 'is_current')
    search_fields = ('nama', 'tahun_akademik')
    ordering = ('-no_siklus',)


@admin.register(Tahap)
class TahapAdmin(admin.ModelAdmin):
    list_display = ('no_urut', 'kode', 'nama', 'durasi_hari', 'is_aktif')
    list_filter = ('is_aktif',)
    ordering = ('no_urut',)


@admin.register(Standar)
class StandarAdmin(admin.ModelAdmin):
    list_display = ('no_urut', 'kode', 'nama_pendek', 'nama', 'is_aktif')
    list_filter = ('is_aktif',)
    search_fields = ('kode', 'nama', 'nama_pendek')
    ordering = ('no_urut',)


@admin.register(ButirPenilaian)
class ButirPenilaianAdmin(admin.ModelAdmin):
    list_display = (
        'kode', 'judul', 'siklus', 'standar', 'jenis_input',
        'bobot', 'is_wajib', 'is_aktif',
    )
    list_filter = ('siklus', 'standar', 'jenis_input', 'is_wajib', 'is_aktif')
    search_fields = ('kode', 'judul')
    autocomplete_fields = ('siklus', 'standar')
    ordering = ('siklus', 'standar', 'no_urut')
