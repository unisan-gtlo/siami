from django import forms

from .models import RtmAgenda, RtmNotulen


class RtmNotulenForm(forms.ModelForm):
    class Meta:
        model = RtmNotulen
        fields = ['isi', 'tipe', 'is_action_item', 'action_pic', 'action_deadline']
        widgets = {
            'isi': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Tulis komentar / usulan / keputusan...'}),
            'tipe': forms.Select(attrs={'style': 'width:auto;'}),
            'is_action_item': forms.CheckboxInput(attrs={'style': 'width:auto;'}),
            'action_pic': forms.Select(attrs={'style': 'width:auto;'}),
            'action_deadline': forms.DateInput(attrs={'type': 'date', 'style': 'width:auto;'}),
        }


class RtmAgendaKeputusanForm(forms.ModelForm):
    class Meta:
        model = RtmAgenda
        fields = ['keputusan']
