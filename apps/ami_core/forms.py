from django import forms

from .models import ButirPenilaian


class ButirPenilaianForm(forms.ModelForm):
    class Meta:
        model = ButirPenilaian
        fields = [
            'standar', 'kode', 'judul', 'deskripsi', 'jenis_input',
            'target_iku', 'target_satuan', 'operator_target',
            'bobot', 'is_wajib', 'is_kuantitatif', 'no_urut',
            'panduan_pengisian', 'rujukan_sn_dikti', 'is_aktif',
        ]
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 2}),
            'panduan_pengisian': forms.Textarea(attrs={'rows': 3}),
        }
