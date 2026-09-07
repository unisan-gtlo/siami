from django import forms

from .models import Fvtb


class FvtbUpdateForm(forms.ModelForm):
    class Meta:
        model = Fvtb
        fields = ['progress_persen', 'update_terakhir']
        widgets = {
            'update_terakhir': forms.Textarea(attrs={'rows': 3}),
        }
