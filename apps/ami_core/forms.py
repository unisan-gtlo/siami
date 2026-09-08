import json
import re

from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from .models import ButirPenilaian, RefEnumerasi

KODE_BARU_PATTERN = re.compile(r'^AMI\d+\.[A-Z]{3}\.[A-Z]\.\d{2}$')


class ButirPenilaianForm(forms.ModelForm):
    metode_verifikasi = forms.MultipleChoiceField(
        choices=[], required=False, widget=forms.CheckboxSelectMultiple,
        help_text='Butir kritis wajib pilih minimal 2. Sumber Data = PD Dikti wajib menyertakan "Verifikasi PD Dikti".',
    )
    sasaran_auditee = forms.MultipleChoiceField(
        choices=[], required=False, widget=forms.CheckboxSelectMultiple,
        initial=['AU-1'],
    )
    dasar_hukum = SimpleArrayField(
        forms.CharField(max_length=300), required=False, delimiter='\n',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Satu sitasi per baris'}),
        help_text='Pasal Permen 39/2025, Standar Mutu SPMI UNISAN, Renstra, SK Rektor — satu per baris.',
    )
    rubrik_skor_json = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 4}),
        label='Rubrik Skor (JSON)',
        help_text='Format: [{"skor":4,"sebutan":"...","deskripsi":"..."}, ...]. Kosongkan untuk pakai rubrik generik.',
    )
    dokumen_bukti_wajib_json = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3}),
        label='Dokumen/Bukti Wajib (JSON)',
        help_text='Format: [{"nama":"...","wajib":true}, ...].',
    )

    class Meta:
        model = ButirPenilaian
        fields = [
            'standar', 'master_standar', 'kode', 'judul', 'deskripsi', 'jenis_input',
            'target_iku', 'target_satuan', 'operator_target',
            'bobot', 'is_wajib', 'is_kuantitatif', 'no_urut',
            'panduan_pengisian', 'rujukan_sn_dikti',
            'domain', 'kelompok_standar', 'sub_standar',
            'pernyataan_butir', 'indikator_ketercapaian',
            'sumber_data', 'tahap_audit', 'lapis_audit',
            'jenis_jawaban', 'butir_kritis', 'status',
        ]
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 2}),
            'panduan_pengisian': forms.Textarea(attrs={'rows': 3}),
            'pernyataan_butir': forms.Textarea(attrs={'rows': 2}),
            'indikator_ketercapaian': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metode_verifikasi'].choices = list(
            RefEnumerasi.objects.filter(kelompok='Metode Verifikasi').order_by('no_urut').values_list('kode', 'nilai'),
        )
        self.fields['sasaran_auditee'].choices = list(
            RefEnumerasi.objects.filter(kelompok='Sasaran Auditee').order_by('no_urut').values_list('kode', 'nilai'),
        )
        if self.instance and self.instance.pk:
            self.fields['metode_verifikasi'].initial = self.instance.metode_verifikasi or []
            self.fields['sasaran_auditee'].initial = self.instance.sasaran_auditee or []
            self.fields['dasar_hukum'].initial = self.instance.dasar_hukum or []
            if self.instance.rubrik_skor:
                self.fields['rubrik_skor_json'].initial = json.dumps(self.instance.rubrik_skor, ensure_ascii=False)
            if self.instance.dokumen_bukti_wajib:
                self.fields['dokumen_bukti_wajib_json'].initial = json.dumps(
                    self.instance.dokumen_bukti_wajib, ensure_ascii=False,
                )

    def clean_kode(self):
        kode = self.cleaned_data['kode']
        # Pola baru cuma diwajibkan untuk butir BARU -- 58 kode lama (mis.
        # "1a.1") tidak boleh diganggu gugat (larangan eksplisit brief
        # migrasi Permen 39/2025).
        if self.instance.pk is None and not KODE_BARU_PATTERN.match(kode):
            raise forms.ValidationError(
                'Kode butir baru wajib mengikuti pola AMI{siklus}.{DOM}.{KEL}.{NN}, '
                'contoh: AMI8.PDD.L.01.',
            )
        return kode

    def clean_rubrik_skor_json(self):
        raw = self.cleaned_data.get('rubrik_skor_json')
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError:
            raise forms.ValidationError('Format JSON tidak valid.')

    def clean_dokumen_bukti_wajib_json(self):
        raw = self.cleaned_data.get('dokumen_bukti_wajib_json')
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError:
            raise forms.ValidationError('Format JSON tidak valid.')

    def clean(self):
        cleaned = super().clean()
        butir_kritis = cleaned.get('butir_kritis')
        metode = cleaned.get('metode_verifikasi') or []
        sumber_data = cleaned.get('sumber_data')
        status = cleaned.get('status')

        if butir_kritis and len(metode) < 2:
            self.add_error('metode_verifikasi', 'Butir kritis wajib punya minimal 2 metode verifikasi (prinsip triangulasi).')
        if sumber_data == 'SD-1' and 'MV-4' not in metode:
            self.add_error('metode_verifikasi', 'Sumber data PD Dikti wajib menyertakan metode "Verifikasi PD Dikti".')
        if cleaned.get('lapis_audit') == 'pelampauan' and butir_kritis:
            self.add_error('butir_kritis', 'Butir lapis Pelampauan (Unggul) tidak boleh berstatus kritis.')
        if status == 'aktif':
            missing = [f for f in ('pernyataan_butir', 'indikator_ketercapaian') if not cleaned.get(f)]
            if missing:
                self.add_error('status', 'Butir berstatus Aktif wajib punya pernyataan butir dan indikator ketercapaian terisi.')
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.metode_verifikasi = self.cleaned_data.get('metode_verifikasi') or None
        obj.sasaran_auditee = self.cleaned_data.get('sasaran_auditee') or None
        obj.dasar_hukum = self.cleaned_data.get('dasar_hukum') or None
        obj.rubrik_skor = self.cleaned_data.get('rubrik_skor_json')
        obj.dokumen_bukti_wajib = self.cleaned_data.get('dokumen_bukti_wajib_json')
        if commit:
            obj.save()
        return obj
