import io
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from apps.ami_core.models import Siklus
from apps.ami_temuan.models import Temuan


def _get_user_ami(request):
    return getattr(request.user, 'ami_profile', None)


@login_required
def laporan_list(request):
    return render(request, 'ami_pelaporan/laporan_list.html', {'active_tab': 'laporan'})


@login_required
def laporan_temuan_pdf(request):
    user_ami = _get_user_ami(request)
    if user_ami is None or user_ami.prodi_id is None:
        messages.error(request, 'Akun Anda belum terhubung ke profil AMI (prodi).')
        return render(request, 'ami_pelaporan/no_profile.html', {'active_tab': 'laporan'})

    siklus = Siklus.objects.filter(is_current=True).first()
    prodi = user_ami.prodi
    temuan_qs = Temuan.objects.filter(siklus=siklus, pengisian__prodi=prodi).order_by('klasifikasi')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph('Laporan Temuan AMI', styles['Title']),
        Paragraph(f'{prodi} &bull; {siklus}', styles['Normal']),
    ]
    if siklus and siklus.regulasi_acuan:
        elements.append(Paragraph(f'Acuan: {siklus.regulasi_acuan.nama_pendek}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    cell_style = styles['Normal'].clone('cell')
    cell_style.fontSize = 8

    def cell(text):
        return Paragraph(escape(text), cell_style)

    data = [['Klasifikasi', 'Judul', 'Deskripsi', 'Tenggat', 'Status']]
    for t in temuan_qs:
        data.append([
            t.klasifikasi,
            cell(t.judul),
            cell(t.deskripsi_problem[:200]),
            str(t.tenggat_tindak_lanjut or '-'),
            t.get_status_display(),
        ])

    if len(data) == 1:
        elements.append(Paragraph('Belum ada temuan untuk prodi ini pada siklus berjalan.', styles['Normal']))
    else:
        table = Table(data, colWidths=[2*cm, 4*cm, 6*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E5A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8F2F8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFCFE')]),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    filename = f'laporan-temuan-{prodi.kode}-siklus{siklus.no_siklus if siklus else "x"}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
