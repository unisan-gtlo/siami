from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Notifikasi, UserAmi

User = get_user_model()


class UserAmiInline(admin.StackedInline):
    """Menampilkan role & atribut AMI langsung di halaman edit Pengguna,
    supaya tidak perlu pindah ke menu 'User AMI' terpisah untuk mengatur role."""

    model = UserAmi
    can_delete = False
    verbose_name_plural = 'Role & Atribut AMI'
    fields = (
        'nidn_nip', 'fakultas', 'prodi',
        ('is_auditor_de', 'is_auditor_visitasi', 'is_upm', 'is_lp3m', 'is_pimpinan'),
        'sertifikasi_auditor', 'pengalaman_audit_thn', 'is_aktif',
    )
    autocomplete_fields = ('fakultas', 'prodi')


class CustomUserAdmin(UserAdmin):
    inlines = [UserAmiInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
