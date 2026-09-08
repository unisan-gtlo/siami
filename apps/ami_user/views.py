from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import UserAmi

# Referensi hak akses per role -- deskriptif, mencerminkan pengecekan yang
# sudah ditegakkan di masing-masing view (is_auditor_de, prodi_id, is_lp3m,
# dst). BUKAN ACL yang bisa dikonfigurasi dari sini.
PERMISSION_MATRIX = {
    'auditor_de': {
        'label': 'Auditor DE',
        'akses': [
            ('1. Identitas Prodi', 'View only'),
            ('2. Self-Assessment', 'View only'),
            ('3. Upload Bukti', 'View only'),
            ('4. Desk Evaluasi', 'Full Edit'),
            ('5. Visitasi', 'No access'),
            ('6. Temuan dan PTK', 'View only'),
            ('7. Tindak Lanjut', 'No access'),
            ('8. RTM', 'No access'),
            ('9. Dashboard', 'No access'),
            ('10. Pelaporan', 'No access'),
            ('11. Manajemen User', 'No access'),
            ('12. Pengarsipan', 'No access'),
        ],
    },
    'auditor_visitasi': {
        'label': 'Auditor Visitasi',
        'akses': [
            ('1. Identitas Prodi', 'View only'),
            ('2. Self-Assessment', 'View only'),
            ('3. Upload Bukti', 'View only'),
            ('4. Desk Evaluasi', 'View only'),
            ('5. Visitasi', 'Full Edit'),
            ('6. Temuan dan PTK', 'View only'),
            ('7. Tindak Lanjut', 'View only'),
            ('8. RTM', 'No access'),
            ('9. Dashboard', 'No access'),
            ('10. Pelaporan', 'No access'),
            ('11. Manajemen User', 'No access'),
            ('12. Pengarsipan', 'No access'),
        ],
    },
    'auditee': {
        'label': 'Auditee (Prodi)',
        'akses': [
            ('1. Identitas Prodi', 'Edit sebagian'),
            ('2. Self-Assessment', 'Full Edit'),
            ('3. Upload Bukti', 'Full Edit'),
            ('4. Desk Evaluasi', 'No access'),
            ('5. Visitasi', 'View + Konfirmasi'),
            ('6. Temuan dan PTK', 'View only'),
            ('7. Tindak Lanjut', 'Update progress (jika PIC)'),
            ('8. RTM', 'No access'),
            ('9. Dashboard', 'No access'),
            ('10. Pelaporan', 'Generate own'),
            ('11. Manajemen User', 'No access'),
            ('12. Pengarsipan', 'No access'),
        ],
    },
    'lp3m': {
        'label': 'LP3M / Pimpinan',
        'akses': [
            ('1. Identitas Prodi', 'View all'),
            ('2. Self-Assessment', 'View all'),
            ('3. Upload Bukti', 'View all'),
            ('4. Desk Evaluasi', 'View all'),
            ('5. Visitasi', 'View all'),
            ('6. Temuan dan PTK', 'View all'),
            ('7. Tindak Lanjut', 'View all'),
            ('8. RTM', 'Full Edit'),
            ('9. Dashboard', 'Full Edit'),
            ('10. Pelaporan', 'Full Edit'),
            ('11. Manajemen User', 'Full Edit'),
            ('12. Pengarsipan', 'View all'),
        ],
    },
}


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


def _is_pengawas(request):
    user_ami = _get_user_ami(request)
    return request.user.is_superuser or (user_ami and (user_ami.is_lp3m or user_ami.is_pimpinan))


@login_required
def user_auditor_list(request):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_user/forbidden.html', {'active_tab': 'user_auditor'})

    role_key = request.GET.get('role', 'auditor_de')
    if role_key not in PERMISSION_MATRIX:
        role_key = 'auditor_de'

    users = UserAmi.objects.select_related('user', 'fakultas').order_by('user__username')

    stats = {
        'total_aktif': users.filter(is_aktif=True).count(),
        'auditor_de': users.filter(is_auditor_de=True, is_aktif=True).count(),
        'auditor_visitasi': users.filter(is_auditor_visitasi=True, is_aktif=True).count(),
        'upm': users.filter(is_upm=True, is_aktif=True).count(),
    }
    auditor_qs = users.filter(is_auditor_de=True) | users.filter(is_auditor_visitasi=True)
    auditor_qs = auditor_qs.distinct()
    pakta_signed = auditor_qs.filter(pakta_integritas_signed_at__isnull=False).count()
    pakta_total = auditor_qs.count()

    role_choices = [(key, r['label']) for key, r in PERMISSION_MATRIX.items()]

    return render(request, 'ami_user/user_auditor_list.html', {
        'users': users, 'stats': stats,
        'pakta_signed': pakta_signed, 'pakta_total': pakta_total,
        'role_choices': role_choices, 'role_key': role_key,
        'selected_role': PERMISSION_MATRIX[role_key],
        'active_tab': 'user_auditor',
    })


@login_required
def sign_pakta_integritas(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or not (user_ami.is_auditor_de or user_ami.is_auditor_visitasi):
        messages.error(request, 'Hanya auditor yang perlu menandatangani Pakta Integritas.')
        return redirect('self_assessment:pengisian_detail')

    if request.method == 'POST':
        user_ami.pakta_integritas_signed_at = timezone.now()
        user_ami.save(update_fields=['pakta_integritas_signed_at', 'updated_at'])
        messages.success(request, 'Pakta Integritas berhasil ditandatangani. Terima kasih atas komitmen Anda.')

    if user_ami.is_auditor_de:
        return redirect('de:penugasan_list')
    return redirect('visitasi:visitasi_saya')
