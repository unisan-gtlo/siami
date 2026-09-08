from django import forms

from .models import DePenilaian


class DePenilaianForm(forms.ModelForm):
    class Meta:
        model = DePenilaian
        # klasifikasi TIDAK diisi manual -- diturunkan otomatis dari skor +
        # butir.butir_kritis lewat hitung_klasifikasi() saat disimpan
        # (lihat views.penilaian_edit), sesuai aturan konversi spesifikasi
        # Kelola Instrumen bagian 3.
        fields = [
            'skor',
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
