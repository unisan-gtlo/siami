from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.ami_core.models import Siklus
from apps.ami_master.models import Prodi
from apps.ami_assessment.models import Pengisian


@login_required
def lp3m_dashboard(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    is_pengawas = user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan)
    if not (request.user.is_superuser or is_pengawas):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_dashboard/forbidden.html', {'active_tab': 'dashboard'})

    siklus = Siklus.objects.filter(is_current=True).first()
    rows = []
    if siklus:
        pengisian_by_prodi = {
            p.prodi_id: p for p in Pengisian.objects.filter(siklus=siklus)
        }
        for prodi in Prodi.objects.filter(is_aktif=True).select_related('fakultas').order_by('fakultas__kode', 'nama'):
            pengisian = pengisian_by_prodi.get(prodi.id)
            rows.append({
                'prodi': prodi,
                'pengisian': pengisian,
            })

    total_prodi = len(rows)
    sudah_mulai = sum(1 for r in rows if r['pengisian'])
    selesai = sum(1 for r in rows if r['pengisian'] and r['pengisian'].status == 'completed')

    return render(request, 'ami_dashboard/dashboard.html', {
        'siklus': siklus,
        'rows': rows,
        'total_prodi': total_prodi,
        'sudah_mulai': sudah_mulai,
        'selesai': selesai,
        'active_tab': 'dashboard',
    })
