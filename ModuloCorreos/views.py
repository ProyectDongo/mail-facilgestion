from django.http import JsonResponse
from django.db.models import Q
from .models import CorreoCopia, PerfilRemitente


def buscar(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'error': 'Parámetro q requerido'}, status=400)

    perfiles = PerfilRemitente.objects.filter(
        Q(nombre__icontains=q) | Q(email__icontains=q)
    )[:5]

    correos = CorreoCopia.objects.filter(
        Q(de__icontains=q) |
        Q(asunto__icontains=q) |
        Q(cuerpo__icontains=q) |
        Q(remitente__nombre__icontains=q) |
        Q(remitente__email__icontains=q)
    ).select_related('remitente')[:20]

    return JsonResponse({
        'query': q,
        'perfiles': [
            {
                'email': p.email,
                'nombre': p.nombre,
                'dominio': p.dominio,
                'total_correos': p.total_correos,
                'ultimo_contacto': str(p.ultimo_contacto),
            }
            for p in perfiles
        ],
        'correos': [
            {
                'de': c.de,
                'para': c.para,
                'asunto': c.asunto,
                'fecha': str(c.fecha),
                'resumen': c.cuerpo[:500],
                'tiene_adjuntos': c.tiene_adjuntos,
                'adjuntos': c.nombres_adjuntos,
            }
            for c in correos
        ]
    })


def estado(request):
    from .models import SyncEstado
    from .models import CorreoCopia, PerfilRemitente
    s = SyncEstado.objects.filter(id=1).first()
    return JsonResponse({
        'ultimo_uid': s.ultimo_uid if s else 0,
        'total_correos': CorreoCopia.objects.count(),
        'total_perfiles': PerfilRemitente.objects.count(),
    })