from django import forms

from .models import DokumenBukti, JawabanButir


# Jenis input butir -> field "nilai_*" yang relevan untuk ditampilkan.
# tabel_dinamis dan auto_iku belum punya UI khusus, sementara jatuh ke
# narasi supaya auditee tetap bisa mengisi sesuatu.
JENIS_INPUT_FIELD_MAP = {
    'numerik': 'nilai_kuantitatif',
    'rasio': 'nilai_kuantitatif',
    'persentase': 'nilai_kuantitatif',
    'auto_iku': 'nilai_kuantitatif',
    'pilihan': 'nilai_pilihan',
    'narasi': 'nilai_narasi',
    'tabel_dinamis': 'nilai_narasi',
}


class JawabanButirForm(forms.ModelForm):
    class Meta:
        model = JawabanButir
        fields = ['nilai_kuantitatif', 'nilai_pilihan', 'nilai_narasi', 'catatan_auditee']
        widgets = {
            'nilai_narasi': forms.Textarea(attrs={'rows': 5}),
            'catatan_auditee': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, jenis_input=None, **kwargs):
        super().__init__(*args, **kwargs)
        relevan = JENIS_INPUT_FIELD_MAP.get(jenis_input)
        if relevan:
            for nama in ('nilai_kuantitatif', 'nilai_pilihan', 'nilai_narasi'):
                if nama != relevan:
                    del self.fields[nama]


class DokumenBuktiForm(forms.ModelForm):
    class Meta:
        model = DokumenBukti
        fields = ['butir', 'nama_dokumen', 'deskripsi', 'jenis_sumber', 'file', 'link_url', 'format']
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, siklus=None, **kwargs):
        super().__init__(*args, **kwargs)
        if siklus is not None:
            self.fields['butir'].queryset = self.fields['butir'].queryset.filter(siklus=siklus)

    def clean(self):
        cleaned = super().clean()
        jenis = cleaned.get('jenis_sumber')
        if jenis == 'upload_file' and not cleaned.get('file'):
            self.add_error('file', 'Wajib diisi untuk jenis sumber "Upload File".')
        if jenis in ('link_drive', 'link_url') and not cleaned.get('link_url'):
            self.add_error('link_url', 'Wajib diisi untuk jenis sumber link.')
        return cleaned
