import io
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.ami_core.models import Siklus
from apps.ami_master.models import Prodi
from apps.ami_temuan.models import Temuan

from .forms import RtmAgendaKeputusanForm, RtmNotulenForm
from .models import Rtm, RtmAgenda, RtmVote


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
            if obj.is_action_item and not obj.action_status:
                obj.action_status = 'open'
            obj.save()
            return redirect('rtm:rtm_detail', rtm_id=rtm.id)
    else:
        form = RtmNotulenForm()

    temuan_qs = Temuan.objects.filter(siklus=rtm.siklus)
    agenda_qs = rtm.agenda_set.all()
    total_anggaran = agenda_qs.aggregate(total=Sum('estimasi_anggaran'))['total'] or 0

    stats = {
        'total_temuan': temuan_qs.count(),
        'prodi_aktif': Prodi.objects.filter(is_aktif=True).count(),
        'kts_mayor_belum': temuan_qs.filter(klasifikasi__in=['KTS_MAYOR', 'KTB']).exclude(status='closed').count(),
        'sesuai_replikasi': temuan_qs.filter(klasifikasi__in=['SESUAI', 'BP'], layak_replikasi=True).count(),
        'total_anggaran': total_anggaran,
    }

    my_votes = {}
    if user_ami:
        my_votes = dict(
            RtmVote.objects.filter(agenda__rtm=rtm, user=user_ami).values_list('agenda_id', 'pilihan'),
        )
    agenda_rows = [{'agenda': a, 'my_vote': my_votes.get(a.id)} for a in agenda_qs]

    notulen_qs = rtm.notulen_set.select_related('user__user', 'action_pic__user')
    action_items = notulen_qs.filter(is_action_item=True)

    return render(request, 'ami_rtm/rtm_detail.html', {
        'rtm': rtm, 'form': form, 'stats': stats,
        'agenda_rows': agenda_rows,
        'notulen_list': notulen_qs,
        'action_items': action_items,
        'is_pengawas': True,
        'keputusan_choices': RtmAgendaKeputusanForm().fields['keputusan'].choices,
        'active_tab': 'rtm',
    })


@login_required
def rtm_vote(request, agenda_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_rtm/forbidden.html', {'active_tab': 'rtm'})

    user_ami = getattr(request.user, 'ami_profile', None)
    agenda = get_object_or_404(RtmAgenda, pk=agenda_id)

    if request.method == 'POST' and user_ami:
        pilihan = request.POST.get('pilihan')
        if pilihan in dict(RtmVote.PILIHAN_CHOICES):
            RtmVote.objects.update_or_create(
                agenda=agenda, user=user_ami, defaults={'pilihan': pilihan},
            )
            agenda.voting_setuju = agenda.vote_set.filter(pilihan='setuju').count()
            agenda.voting_tidak = agenda.vote_set.filter(pilihan='tidak').count()
            agenda.voting_abstain = agenda.vote_set.filter(pilihan='abstain').count()
            agenda.save(update_fields=['voting_setuju', 'voting_tidak', 'voting_abstain'])
            messages.success(request, 'Vote Anda tersimpan.')

    return redirect('rtm:rtm_detail', rtm_id=agenda.rtm_id)


@login_required
def rtm_agenda_keputusan(request, agenda_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_rtm/forbidden.html', {'active_tab': 'rtm'})

    agenda = get_object_or_404(RtmAgenda, pk=agenda_id)

    if request.method == 'POST':
        form = RtmAgendaKeputusanForm(request.POST, instance=agenda)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.keputusan_pada = timezone.now()
            obj.save()
            messages.success(request, f'Keputusan untuk "{agenda.judul}" ditetapkan.')

    return redirect('rtm:rtm_detail', rtm_id=agenda.rtm_id)


@login_required
def rtm_export_pdf(request, rtm_id):
    if not _is_pengawas(request):
        messages.error(request, 'Halaman ini hanya untuk LP3M/Pimpinan.')
        return render(request, 'ami_rtm/forbidden.html', {'active_tab': 'rtm'})

    rtm = get_object_or_404(Rtm, pk=rtm_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f'Notulen RTM — {rtm.judul}', styles['Title']),
        Paragraph(f'{rtm.tgl_rapat} &bull; {rtm.tempat or "-"} &bull; {rtm.siklus}', styles['Normal']),
        Spacer(1, 0.5*cm),
    ]

    cell_style = styles['Normal'].clone('cell')
    cell_style.fontSize = 8

    def cell(text):
        return Paragraph(escape(str(text)), cell_style)

    elements.append(Paragraph('Agenda Keputusan Strategis', styles['Heading2']))
    agenda_data = [['Judul', 'Prioritas', 'PIC', 'Estimasi Anggaran', 'Target', 'Keputusan']]
    for a in rtm.agenda_set.all():
        agenda_data.append([
            cell(a.judul), a.get_prioritas_display() or '-', cell(a.pic or a.pic_unit or '-'),
            f'Rp {a.estimasi_anggaran:,.0f}' if a.estimasi_anggaran else '-',
            str(a.target_completion or '-'), a.get_keputusan_display() or 'Pending',
        ])
    if len(agenda_data) > 1:
        table = Table(agenda_data, colWidths=[4*cm, 2*cm, 3*cm, 2.5*cm, 2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E5A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8F2F8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFCFE')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph('Belum ada agenda.', styles['Normal']))

    elements.append(Spacer(1, 0.7*cm))
    elements.append(Paragraph('Notulen', styles['Heading2']))
    notulen_data = [['Waktu', 'Peserta', 'Isi']]
    for n in rtm.notulen_set.select_related('user__user'):
        notulen_data.append([str(n.waktu_kirim.strftime('%H:%M')), cell(n.user), cell(n.isi)])
    if len(notulen_data) > 1:
        table2 = Table(notulen_data, colWidths=[2*cm, 3*cm, 10*cm])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E5A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8F2F8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFCFE')]),
        ]))
        elements.append(table2)
    else:
        elements.append(Paragraph('Belum ada notulen.', styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    filename = f'notulen-rtm-{rtm.id}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
