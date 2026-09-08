from django import forms

from .models import Prodi


class ProdiIdentitasForm(forms.ModelForm):
    class Meta:
        model = Prodi
        fields = [
            'sk_pendirian_no', 'sk_pendirian_tgl', 'tanggal_mulai_beroperasi',
            'akreditasi_lembaga', 'akreditasi_peringkat',
            'akreditasi_no_sk', 'akreditasi_tgl_sk', 'akreditasi_berlaku_sd',
            'status_akreditasi',
        ]
        widgets = {
            'sk_pendirian_tgl': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_mulai_beroperasi': forms.DateInput(attrs={'type': 'date'}),
            'akreditasi_tgl_sk': forms.DateInput(attrs={'type': 'date'}),
            'akreditasi_berlaku_sd': forms.DateInput(attrs={'type': 'date'}),
        }
