from django import forms

from .models import RtmNotulen


class RtmNotulenForm(forms.ModelForm):
    class Meta:
        model = RtmNotulen
        fields = ['isi', 'tipe']
        widgets = {
            'isi': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Tulis komentar / usulan / keputusan...'}),
        }
