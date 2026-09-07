from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProdiIdentitasForm


@login_required
def identitas_prodi(request):
    user_ami = getattr(request.user, 'ami_profile', None)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_master/no_profile.html', {'active_tab': 'identitas'})

    prodi = user_ami.prodi

    if request.method == 'POST':
        form = ProdiIdentitasForm(request.POST, instance=prodi)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data identitas prodi tersimpan.')
            return redirect('identitas:prodi')
    else:
        form = ProdiIdentitasForm(instance=prodi)

    return render(request, 'ami_master/identitas_prodi.html', {
        'prodi': prodi, 'form': form, 'active_tab': 'identitas',
    })
