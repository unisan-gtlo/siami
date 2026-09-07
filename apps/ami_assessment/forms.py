from django import forms

from .models import JawabanButir


class JawabanButirForm(forms.ModelForm):
    class Meta:
        model = JawabanButir
        fields = ['nilai_kuantitatif', 'nilai_pilihan', 'nilai_narasi', 'catatan_auditee']
        widgets = {
            'nilai_narasi': forms.Textarea(attrs={'rows': 5}),
            'catatan_auditee': forms.Textarea(attrs={'rows': 3}),
        }
