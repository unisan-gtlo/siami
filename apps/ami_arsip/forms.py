from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from .models import ArsipMetadata


class ArsipUploadForm(forms.ModelForm):
    tags = SimpleArrayField(
        forms.CharField(max_length=50), delimiter=',', required=False,
        help_text='Pisahkan dengan koma, mis: sk, rektor, siklus8',
    )

    class Meta:
        model = ArsipMetadata
        fields = ['siklus', 'prodi', 'kategori', 'nama_dokumen', 'deskripsi', 'file', 'tags']
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 2}),
        }
