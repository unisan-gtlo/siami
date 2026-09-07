from django.contrib import admin

from .models import Notifikasi, UserAmi


@admin.register(UserAmi)
class UserAmiAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'nidn_nip', 'fakultas', 'prodi',
        'is_auditor_de', 'is_auditor_visitasi', 'is_upm', 'is_lp3m', 'is_pimpinan',
        'is_aktif',
    )
    list_filter = (
        'is_auditor_de', 'is_auditor_visitasi', 'is_upm', 'is_lp3m', 'is_pimpinan',
        'is_aktif', 'fakultas',
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'nidn_nip')
    autocomplete_fields = ('user', 'fakultas', 'prodi')


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ('judul', 'to_user', 'tipe', 'priority', 'is_read', 'created_at')
    list_filter = ('tipe', 'priority', 'is_read', 'channel_email', 'channel_wa')
    search_fields = ('judul', 'isi', 'to_user__user__username')
    autocomplete_fields = ('to_user',)
