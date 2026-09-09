from django import forms

from apps.ami_assessment.models import Pengisian
from apps.ami_master.models import Fakultas, Prodi
from apps.ami_user.models import UserAmi

from .models import DePenilaian, DePenugasan


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


class DePenugasanForm(forms.Form):
    """Menugaskan auditor DE ke satu auditee (Prodi/Fakultas/Universitas)
    untuk siklus aktif -- pengganti Django admin untuk aksi ini. Pengisian
    auditee-nya sendiri boleh belum ada (LP3M bisa menugaskan auditor
    sebelum auditee mulai isi self-assessment), jadi di sini cuma pilih
    cakupan + prodi/fakultas, bukan Pengisian langsung."""

    cakupan = forms.ChoiceField(label='Cakupan Auditee', choices=Pengisian.CAKUPAN_CHOICES)
    prodi = forms.ModelChoiceField(label='Program Studi', queryset=Prodi.objects.filter(is_aktif=True), required=False)
    fakultas = forms.ModelChoiceField(label='UPPS/Fakultas', queryset=Fakultas.objects.filter(is_aktif=True), required=False)

    auditor = forms.ModelChoiceField(
        label='Auditor DE', queryset=UserAmi.objects.filter(is_auditor_de=True, is_aktif=True).select_related('user'),
    )
    role_dalam_tim = forms.ChoiceField(label='Peran dalam Tim', choices=DePenugasan.ROLE_CHOICES)

    sk_no = forms.CharField(label='Nomor SK Penugasan', max_length=100)
    sk_tgl = forms.DateField(label='Tanggal SK', widget=forms.DateInput(attrs={'type': 'date'}))
    tgl_mulai_de = forms.DateField(label='Tanggal Mulai DE', widget=forms.DateInput(attrs={'type': 'date'}))
    tenggat_de = forms.DateField(label='Tenggat DE', widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        cleaned = super().clean()
        cakupan = cleaned.get('cakupan')
        if cakupan == 'prodi' and not cleaned.get('prodi'):
            self.add_error('prodi', 'Wajib dipilih untuk cakupan Program Studi.')
        elif cakupan == 'fakultas' and not cleaned.get('fakultas'):
            self.add_error('fakultas', 'Wajib dipilih untuk cakupan UPPS/Fakultas.')
        return cleaned
