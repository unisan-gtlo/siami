from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.ami_core.models import Siklus

from .forms import FvtbUpdateForm
from .models import Fvtb, Temuan


@login_required
def temuan_list(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_temuan/no_profile.html', {'active_tab': 'temuan'})

    siklus = Siklus.objects.filter(is_current=True).first()
    temuan_qs = Temuan.objects.filter(
        siklus=siklus, pengisian__prodi=user_ami.prodi,
    ).select_related('butir').prefetch_related('fvtb_set').order_by('klasifikasi', '-created_at')

    stats = {kode: temuan_qs.filter(klasifikasi=kode).count() for kode in ('KTB', 'KTS', 'OB', 'BP')}

    return render(request, 'ami_temuan/temuan_list.html', {
        'temuan_list': temuan_qs, 'stats': stats, 'active_tab': 'temuan',
    })


@login_required
def fvtb_update(request, fvtb_id):
    user_ami = getattr(request.user, 'ami_profile', None)
    fvtb = get_object_or_404(Fvtb, pk=fvtb_id, pic=user_ami)
    progress_sebelum = fvtb.progress_persen

    if request.method == 'POST':
        form = FvtbUpdateForm(request.POST, instance=fvtb)
        if form.is_valid():
            # form.is_valid() sudah menulis field yang dibersihkan ke fvtb
            # (instance yang sama) lewat _post_clean() -- progress_sebelum
            # WAJIB dibaca sebelum baris ini, bukan sesudah is_valid().
            obj = form.save(commit=False)
            obj.update_pada = timezone.now()
            if obj.progress_persen >= 100:
                obj.status = 'check'
            obj.save()
            obj.progress_log_set.create(
                progress_sebelum=progress_sebelum,
                progress_sesudah=obj.progress_persen,
                update_text=obj.update_terakhir or '',
                diupdate_oleh=user_ami,
            )
            messages.success(request, 'Progress tindak lanjut tersimpan.')
            return redirect('temuan:temuan_list')
    else:
        form = FvtbUpdateForm(instance=fvtb)

    return render(request, 'ami_temuan/fvtb_update.html', {
        'form': form, 'fvtb': fvtb, 'active_tab': 'temuan',
    })
