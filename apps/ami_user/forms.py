from django import forms

from apps.ami_master.models import Fakultas, Prodi


class TambahAuditorForm(forms.Form):
    """Form gabungan membuat auth.User + UserAmi sekaligus -- pengganti
    portal untuk `/admin/auth/user/add/` yang sebelumnya jadi satu-satunya
    cara LP3M menambah auditor lewat UI."""

    first_name = forms.CharField(label='Nama Depan', max_length=150)
    last_name = forms.CharField(label='Nama Belakang', max_length=150, required=False)
    username = forms.CharField(label='Username', max_length=150)
    email = forms.EmailField(label='Email', required=False)
    nidn_nip = forms.CharField(label='NIDN/NIP', max_length=30, required=False)
    fakultas = forms.ModelChoiceField(label='Fakultas', queryset=Fakultas.objects.filter(is_aktif=True), required=False)
    prodi = forms.ModelChoiceField(label='Prodi (bila auditee)', queryset=Prodi.objects.filter(is_aktif=True), required=False)

    is_auditor_de = forms.BooleanField(label='Auditor Desk Evaluasi', required=False)
    is_auditor_visitasi = forms.BooleanField(label='Auditor Visitasi', required=False)
    is_upm = forms.BooleanField(label='UPM Fakultas', required=False)

    sertifikasi_auditor = forms.CharField(label='Sertifikasi Auditor', max_length=100, required=False)
    pengalaman_audit_thn = forms.IntegerField(label='Pengalaman Audit (tahun)', required=False, min_value=0)

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username sudah dipakai.')
        return username

    def clean_nidn_nip(self):
        from .models import UserAmi
        nidn = self.cleaned_data.get('nidn_nip', '').strip()
        if nidn and UserAmi.objects.filter(nidn_nip=nidn).exists():
            raise forms.ValidationError('NIDN/NIP ini sudah terdaftar.')
        return nidn or None


class EditUserAmiForm(forms.Form):
    """Edit profil + role user yang sudah ada -- username/password tidak
    disentuh di sini (username immutable, password lewat alur reset
    terpisah)."""

    first_name = forms.CharField(label='Nama Depan', max_length=150)
    last_name = forms.CharField(label='Nama Belakang', max_length=150, required=False)
    email = forms.EmailField(label='Email', required=False)
    nidn_nip = forms.CharField(label='NIDN/NIP', max_length=30, required=False)
    fakultas = forms.ModelChoiceField(label='Fakultas', queryset=Fakultas.objects.filter(is_aktif=True), required=False)
    prodi = forms.ModelChoiceField(label='Prodi (bila auditee)', queryset=Prodi.objects.filter(is_aktif=True), required=False)

    is_auditor_de = forms.BooleanField(label='Auditor Desk Evaluasi', required=False)
    is_auditor_visitasi = forms.BooleanField(label='Auditor Visitasi', required=False)
    is_upm = forms.BooleanField(label='UPM Fakultas', required=False)
    is_lp3m = forms.BooleanField(label='LP3M', required=False)
    is_pimpinan = forms.BooleanField(label='Pimpinan', required=False)

    sertifikasi_auditor = forms.CharField(label='Sertifikasi Auditor', max_length=100, required=False)
    pengalaman_audit_thn = forms.IntegerField(label='Pengalaman Audit (tahun)', required=False, min_value=0)
    is_aktif = forms.BooleanField(label='Aktif', required=False)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def clean_nidn_nip(self):
        from .models import UserAmi
        nidn = self.cleaned_data.get('nidn_nip', '').strip()
        if nidn:
            qs = UserAmi.objects.filter(nidn_nip=nidn)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('NIDN/NIP ini sudah terdaftar untuk user lain.')
        return nidn or None


class ImportExcelAuditorForm(forms.Form):
    file = forms.FileField(label='File Excel (.xlsx)')
