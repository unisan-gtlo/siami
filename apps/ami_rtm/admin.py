from django.contrib import admin

from .models import Rtm, RtmAgenda, RtmNotulen, RtmVote


class RtmAgendaInline(admin.TabularInline):
    model = RtmAgenda
    extra = 0
    fields = ('no_urut', 'judul', 'prioritas', 'pic', 'keputusan')
    autocomplete_fields = ('pic',)


@admin.register(Rtm)
class RtmAdmin(admin.ModelAdmin):
    list_display = ('judul', 'siklus', 'tgl_rapat', 'status', 'pemimpin', 'jml_keputusan')
    list_filter = ('siklus', 'status')
    search_fields = ('judul',)
    autocomplete_fields = ('siklus', 'pemimpin', 'notulis')
    inlines = [RtmAgendaInline]


@admin.register(RtmAgenda)
class RtmAgendaAdmin(admin.ModelAdmin):
    list_display = ('judul', 'rtm', 'prioritas', 'pic', 'keputusan')
    list_filter = ('prioritas', 'keputusan')
    search_fields = ('judul', 'rtm__judul')
    autocomplete_fields = ('rtm', 'pic')


@admin.register(RtmNotulen)
class RtmNotulenAdmin(admin.ModelAdmin):
    list_display = ('rtm', 'user', 'tipe', 'is_action_item', 'action_status', 'waktu_kirim')
    list_filter = ('tipe', 'is_action_item', 'action_status')
    search_fields = ('isi', 'rtm__judul')
    autocomplete_fields = ('rtm', 'user', 'action_pic', 'reply_to')


@admin.register(RtmVote)
class RtmVoteAdmin(admin.ModelAdmin):
    list_display = ('agenda', 'user', 'pilihan', 'voted_at')
    list_filter = ('pilihan',)
    autocomplete_fields = ('agenda', 'user')
