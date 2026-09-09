from django.contrib import admin

from .models import ArsipMetadata, PencarianArsipLog


@admin.register(ArsipMetadata)
class ArsipMetadataAdmin(admin.ModelAdmin):
    list_display = (
        'nama_dokumen', 'kategori', 'siklus', 'prodi',
        'is_publik', 'synced_to_arsip', 'diunggah_pada',
    )
    list_filter = ('kategori', 'is_publik', 'synced_to_arsip', 'is_permanen', 'siklus')
    search_fields = ('nama_dokumen', 'deskripsi', 'fulltext_content')
    autocomplete_fields = ('siklus', 'prodi', 'master_standar', 'diunggah_oleh')
    readonly_fields = ('fulltext_search', 'diunggah_pada')


@admin.register(PencarianArsipLog)
class PencarianArsipLogAdmin(admin.ModelAdmin):
    list_display = ('query', 'jumlah_hasil', 'siklus', 'dicari_oleh', 'created_at')
    list_filter = ('siklus',)
    readonly_fields = ('created_at',)
