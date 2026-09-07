from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.ami_core.models import Siklus
from apps.ami_temuan.models import Temuan

from .forms import RtmNotulenForm
from .models import Rtm


def _is_pengawas(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    return request.user.is_superuser or (user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan))


@login_required
def rtm_list(request):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_rtm/forbidden.html', {'active_tab': 'rtm'})

    siklus = Siklus.objects.filter(is_current=True).first()
    rtm_qs = Rtm.objects.filter(siklus=siklus).order_by('-tgl_rapat') if siklus else Rtm.objects.none()

    return render(request, 'ami_rtm/rtm_list.html', {
        'rtm_list': rtm_qs, 'active_tab': 'rtm',
    })


@login_required
def rtm_detail(request, rtm_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_rtm/forbidden.html', {'active_tab': 'rtm'})

    rtm = get_object_or_404(Rtm, pk=rtm_id)
    user_ami = getattr(request.user, 'ami_profile', None)

    if request.method == 'POST':
        form = RtmNotulenForm(request.POST)
        if form.is_valid() and user_ami:
            obj = form.save(commit=False)
            obj.rtm = rtm
            obj.user = user_ami
            obj.save()
            return redirect('rtm:rtm_detail', rtm_id=rtm.id)
    else:
        form = RtmNotulenForm()

    temuan_stats = Temuan.objects.filter(siklus=rtm.siklus)
    stats = {
        'total_temuan': temuan_stats.count(),
        'ktb_belum': temuan_stats.filter(klasifikasi='KTB').exclude(status='closed').count(),
        'bp': temuan_stats.filter(klasifikasi='BP').count(),
    }

    return render(request, 'ami_rtm/rtm_detail.html', {
        'rtm': rtm, 'form': form, 'stats': stats,
        'agenda_list': rtm.agenda_set.all(),
        'notulen_list': rtm.notulen_set.select_related('user__user'),
        'active_tab': 'rtm',
    })
