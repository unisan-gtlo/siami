from django import forms

from .models import DePenilaian


class DePenilaianForm(forms.ModelForm):
    class Meta:
        model = DePenilaian
        fields = [
            'skor', 'klasifikasi',
            'plor_problem', 'plor_location', 'plor_objective', 'plor_reference',
            'catatan_auditor', 'rekomendasi_visitasi',
        ]
        widgets = {
            'plor_problem': forms.Textarea(attrs={'rows': 3}),
            'plor_location': forms.TextInput(),
            'plor_objective': forms.TextInput(),
            'plor_reference': forms.TextInput(),
            'catatan_auditor': forms.Textarea(attrs={'rows': 3}),
            'rekomendasi_visitasi': forms.Textarea(attrs={'rows': 3}),
        }
