from .models import Siklus


def siklus_aktif(request):
    siklus = Siklus.objects.filter(is_current=True).only('nama', 'tahun_akademik').first()
    if siklus is None:
        return {'siklus_aktif': None}
    return {'siklus_aktif': f'{siklus.nama} — {siklus.tahun_akademik}'}
