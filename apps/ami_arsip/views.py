from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.ami_assessment.models import Pengisian
from apps.ami_core.models import MasterStandar, Siklus
from apps.ami_master.models import Prodi
from apps.ami_temuan.models import Temuan

from .forms import ArsipUploadForm
from .models import ArsipMetadata, PencarianArsipLog


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


def _has_read_access(request):
    user_ami = _get_user_ami(request)
    return request.user.is_superuser or (user_ami and (
        user_ami.is_lp3m or user_ami.is_pimpinan
        or user_ami.is_auditor_de or user_ami.is_auditor_visitasi
    ))


def _can_upload(request):
    user_ami = _get_user_ami(request)
    return request.user.is_superuser or (user_ami and user_ami.is_lp3m)


def _jumlah_prodi(siklus):
    return Pengisian.objects.filter(siklus=siklus, cakupan='prodi').values('prodi').distinct().count()


@login_required
def arsip_list(request):
    if not _has_read_access(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan/Auditor.')
        return render(request, 'ami_arsip/forbidden.html', {'active_tab': 'arsip'})

    q = request.GET.get('q', '').strip()
    f_siklus = request.GET.get('siklus', '')
    f_kategori = request.GET.get('kategori', '')
    f_prodi = request.GET.get('prodi', '')
    f_standar = request.GET.get('standar', '')

    results = None
    if q or f_siklus or f_kategori or f_prodi or f_standar:
        qs = ArsipMetadata.objects.select_related('siklus', 'prodi', 'master_standar')
        if q:
            query = SearchQuery(q, config='indonesian')
            qs = qs.filter(fulltext_search=query).annotate(rank=SearchRank('fulltext_search', query)).order_by('-rank')
        else:
            qs = qs.order_by('-diunggah_pada')
        if f_siklus:
            qs = qs.filter(siklus_id=f_siklus)
        if f_kategori:
            qs = qs.filter(kategori=f_kategori)
        if f_prodi:
            qs = qs.filter(prodi_id=f_prodi)
        if f_standar:
            qs = qs.filter(master_standar_id=f_standar)

        total_hasil = qs.count()
        results = qs[:30]

        if q:
            PencarianArsipLog.objects.create(
                query=q, jumlah_hasil=total_hasil,
                siklus_id=f_siklus or None, dicari_oleh=_get_user_ami(request),
            )

    siklus_rows = []
    for siklus in Siklus.objects.order_by('-no_siklus'):
        siklus_rows.append({
            'siklus': siklus,
            'dokumen_count': ArsipMetadata.objects.filter(siklus=siklus).count(),
            'temuan_count': Temuan.objects.filter(siklus=siklus).count(),
            'jumlah_prodi': _jumlah_prodi(siklus),
        })

    total_size = ArsipMetadata.objects.aggregate(total=Sum('file_size_bytes'))['total'] or 0

    kategori_stats = [
        (kode, label, ArsipMetadata.objects.filter(kategori=kode).count())
        for kode, label in ArsipMetadata.KATEGORI_CHOICES
    ]

    stats = {
        'total_dokumen': ArsipMetadata.objects.count(),
        'total_size_mb': round(total_size / (1024 * 1024), 1),
        'siklus_dengan_arsip': sum(1 for r in siklus_rows if r['dokumen_count'] > 0),
        'synced': ArsipMetadata.objects.filter(synced_to_arsip=True).count(),
    }

    return render(request, 'ami_arsip/arsip_list.html', {
        'siklus_rows': siklus_rows, 'stats': stats, 'kategori_stats': kategori_stats,
        'q': q, 'results': results,
        'f_siklus': f_siklus, 'f_kategori': f_kategori, 'f_prodi': f_prodi, 'f_standar': f_standar,
        'siklus_list': Siklus.objects.order_by('-no_siklus'),
        'prodi_list': Prodi.objects.filter(is_aktif=True).order_by('nama'),
        'standar_list': MasterStandar.objects.order_by('no_urut'),
        'riwayat_pencarian': PencarianArsipLog.objects.select_related('siklus')[:5],
        'can_upload': _can_upload(request),
        'active_tab': 'arsip',
    })


@login_required
def arsip_siklus_detail(request, siklus_id):
    if not _has_read_access(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan/Auditor.')
        return render(request, 'ami_arsip/forbidden.html', {'active_tab': 'arsip'})

    siklus = get_object_or_404(Siklus, pk=siklus_id)

    dokumen = ArsipMetadata.objects.filter(siklus=siklus).select_related('prodi', 'master_standar').order_by('-diunggah_pada')
    f_kategori = request.GET.get('kategori', '')
    if f_kategori:
        dokumen = dokumen.filter(kategori=f_kategori)

    kategori_stats = [
        (kode, label, ArsipMetadata.objects.filter(siklus=siklus, kategori=kode).count())
        for kode, label in ArsipMetadata.KATEGORI_CHOICES
    ]

    return render(request, 'ami_arsip/arsip_siklus_detail.html', {
        'siklus': siklus, 'dokumen': dokumen,
        'jumlah_prodi': _jumlah_prodi(siklus),
        'temuan_count': Temuan.objects.filter(siklus=siklus).count(),
        'kategori_stats': kategori_stats, 'f_kategori': f_kategori,
        'can_upload': _can_upload(request),
        'active_tab': 'arsip',
    })


@login_required
def arsip_upload(request):
    if not _can_upload(request):
        messages.error(request, 'Hanya LP3M yang bisa mengunggah dokumen arsip.')
        return redirect('arsip:arsip_list')

    user_ami = _get_user_ami(request)

    if request.method == 'POST':
        form = ArsipUploadForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.diunggah_oleh = user_ami
            obj.file_size_bytes = obj.file.size
            obj.file_mime_type = getattr(obj.file.file, 'content_type', '') or ''
            obj.save()
            messages.success(request, f'Dokumen "{obj.nama_dokumen}" berhasil diarsipkan.')
            return redirect('arsip:arsip_list')
    else:
        form = ArsipUploadForm()

    return render(request, 'ami_arsip/arsip_upload.html', {
        'form': form, 'active_tab': 'arsip',
    })
