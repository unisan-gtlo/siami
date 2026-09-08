from django import forms

from .models import Fvtb, Temuan


class FvtbUpdateForm(forms.ModelForm):
    class Meta:
        model = Fvtb
        fields = ['progress_persen', 'update_terakhir']
        widgets = {
            'update_terakhir': forms.Textarea(attrs={'rows': 3}),
        }


class FvtbVerifyForm(forms.ModelForm):
    class Meta:
        model = Fvtb
        fields = ['catatan_verifikasi']
        widgets = {
            'catatan_verifikasi': forms.Textarea(attrs={'rows': 3}),
        }


class TemuanFromDePenilaianForm(forms.ModelForm):
    class Meta:
        model = Temuan
        fields = [
            'klasifikasi', 'judul', 'deskripsi_problem', 'lokasi_temuan',
            'standar_dilanggar', 'bukti_referensi', 'dampak', 'urgensi',
            'tenggat_tindak_lanjut', 'layak_replikasi',
        ]
        widgets = {
            'deskripsi_problem': forms.Textarea(attrs={'rows': 3}),
            'bukti_referensi': forms.Textarea(attrs={'rows': 2}),
            'dampak': forms.Textarea(attrs={'rows': 2}),
            'tenggat_tindak_lanjut': forms.DateInput(attrs={'type': 'date'}),
        }
