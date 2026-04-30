import json
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import CorreoCopia, PerfilRemitente, SyncEstado, DocumentoLegal


# ─────────────────────────────────────────────
# ESTADO GENERAL DEL SISTEMA
# ─────────────────────────────────────────────
def estado(request):
    s = SyncEstado.objects.filter(id=1).first()
    temas = list(
        CorreoCopia.objects.values('tema')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    return JsonResponse({
        'ultimo_uid': s.ultimo_uid if s else 0,
        'total_correos': CorreoCopia.objects.count(),
        'total_perfiles': PerfilRemitente.objects.count(),
        'correos_urgentes': CorreoCopia.objects.filter(es_pendiente=True).count(),
        'correos_sin_clasificar': CorreoCopia.objects.filter(clasificado=False).count(),
        'temas_top': temas,
    })


# ─────────────────────────────────────────────
# BÚSQUEDA GENERAL — para IAs
# ─────────────────────────────────────────────
def buscar(request):
    q = request.GET.get('q', '').strip()
    tema = request.GET.get('tema', '').strip()
    solo_urgentes = request.GET.get('urgentes', '').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 50)

    if not q and not tema and not solo_urgentes:
        return JsonResponse({'error': 'Se requiere al menos un parámetro: q, tema o urgentes=true'}, status=400)

    # --- Perfiles ---
    perfiles_qs = PerfilRemitente.objects.all()
    if q:
        perfiles_qs = perfiles_qs.filter(
            Q(nombre__icontains=q) |
            Q(email__icontains=q) |
            Q(empresa__icontains=q) |
            Q(rut__icontains=q)
        )
    perfiles = perfiles_qs.order_by('-total_correos')[:5]

    # --- Correos ---
    correos_qs = CorreoCopia.objects.select_related('remitente')
    if q:
        correos_qs = correos_qs.filter(
            Q(de__icontains=q) |
            Q(asunto__icontains=q) |
            Q(cuerpo__icontains=q) |
            Q(remitente__nombre__icontains=q) |
            Q(remitente__email__icontains=q)
        )
    if tema:
        correos_qs = correos_qs.filter(tema=tema)
    if solo_urgentes:
        correos_qs = correos_qs.filter(es_pendiente=True)

    correos = correos_qs.order_by('-fecha')[:limit]

    return JsonResponse({
        'query': q,
        'filtros': {'tema': tema, 'solo_urgentes': solo_urgentes},
        'total_resultados': correos_qs.count(),
        'perfiles': [_serializar_perfil_resumido(p) for p in perfiles],
        'correos': [_serializar_correo(c) for c in correos],
    })


# ─────────────────────────────────────────────
# PERFIL COMPLETO DE UN REMITENTE
# ─────────────────────────────────────────────
def perfil(request, email):
    try:
        p = PerfilRemitente.objects.get(email=email.lower())
    except PerfilRemitente.DoesNotExist:
        return JsonResponse({'error': f'Perfil no encontrado: {email}'}, status=404)

    correos = CorreoCopia.objects.filter(remitente=p).order_by('-fecha')
    total = correos.count()
    urgentes = correos.filter(es_pendiente=True)

    temas_raw = correos.values('tema').annotate(total=Count('id')).order_by('-total')
    temas = {t['tema']: t['total'] for t in temas_raw}

    ultimos = correos[:10]

    temas_frecuentes = {}
    try:
        temas_frecuentes = json.loads(p.temas_frecuentes) if p.temas_frecuentes else {}
    except Exception:
        pass

    return JsonResponse({
        'perfil': {
            'email': p.email,
            'nombre': p.nombre,
            'empresa': p.empresa,
            'rut': p.rut,
            'dominio': p.dominio,
            'tipo': p.tipo,
            'es_empresa': p.es_empresa,
            'tono_predominante': p.tono_predominante,
            'frecuencia': p.frecuencia,
            'nivel_prioridad': p.nivel_prioridad,
            'total_correos': p.total_correos,
            'pendientes_activos': p.pendientes_activos,
            'primer_contacto': str(p.primer_contacto),
            'ultimo_contacto': str(p.ultimo_contacto),
            'temas_frecuentes': temas_frecuentes,
            'resumen_perfil': p.resumen_perfil,
            'ultima_solicitud': p.ultima_solicitud,
        },
        'estadisticas': {
            'total_correos': total,
            'urgentes': urgentes.count(),
            'temas': temas,
        },
        'correos_urgentes': [_serializar_correo(c) for c in urgentes[:5]],
        'ultimos_correos': [_serializar_correo(c) for c in ultimos],
    })


# ─────────────────────────────────────────────
# LISTADO DE PERFILES — con filtros
# ─────────────────────────────────────────────
def perfiles(request):
    tipo = request.GET.get('tipo', '').strip()
    prioridad = request.GET.get('prioridad', '').strip()
    con_pendientes = request.GET.get('con_pendientes', '').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 100)

    qs = PerfilRemitente.objects.all()
    if tipo:
        qs = qs.filter(tipo=tipo)
    if prioridad:
        qs = qs.filter(nivel_prioridad=prioridad)
    if con_pendientes:
        qs = qs.filter(pendientes_activos__gt=0)

    qs = qs.order_by('-total_correos')[:limit]

    return JsonResponse({
        'total': qs.count(),
        'perfiles': [_serializar_perfil_resumido(p) for p in qs],
    })


# ─────────────────────────────────────────────
# CORREOS URGENTES / PENDIENTES
# ─────────────────────────────────────────────
def urgentes(request):
    tema = request.GET.get('tema', '').strip()
    limit = min(int(request.GET.get('limit', 30)), 100)

    qs = CorreoCopia.objects.filter(es_pendiente=True).select_related('remitente')
    if tema:
        qs = qs.filter(tema=tema)
    qs = qs.order_by('-fecha')[:limit]

    return JsonResponse({
        'total': CorreoCopia.objects.filter(es_pendiente=True).count(),
        'correos': [_serializar_correo(c) for c in qs],
    })


# ─────────────────────────────────────────────
# DOCUMENTOS LEGALES — búsqueda
# ─────────────────────────────────────────────
def documentos(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    qs = DocumentoLegal.objects.filter(activo=True)
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(tags__icontains=q) |
            Q(contenido__icontains=q)
        )
    if tipo:
        qs = qs.filter(tipo=tipo)

    docs = qs.order_by('-subido_en')[:20]

    return JsonResponse({
        'total': qs.count(),
        'documentos': [
            {
                'id': d.id,
                'titulo': d.titulo,
                'tipo': d.tipo,
                'descripcion': d.descripcion,
                'tags': d.tags,
                'url': d.url,
                'fragmento': d.contenido[:500] if d.contenido else '',
                'subido_en': str(d.subido_en),
            }
            for d in docs
        ],
    })


# ─────────────────────────────────────────────
# CONTEXTO PARA IA — endpoint principal para IAs
# devuelve todo lo relevante en un solo JSON limpio
# ─────────────────────────────────────────────
def contexto_ia(request):
    """
    Endpoint diseñado para que las IAs consulten con lenguaje natural.
    Parámetros:
      - q: texto libre (nombre, email, tema)
      - tipo: cliente | proveedor | organismo_publico | interno
      - tema: f29 | finiquito | licencia_medica | etc.
      - urgentes: true
    """
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    tema = request.GET.get('tema', '').strip()
    solo_urgentes = request.GET.get('urgentes', '').lower() == 'true'

    respuesta = {
        'instrucciones': (
            'Estos son datos reales de correos de una empresa contable. '
            'Usa esta información para responder preguntas sobre clientes, '
            'trámites pendientes, y documentos.'
        ),
        'perfiles': [],
        'correos_relevantes': [],
        'documentos_legales': [],
        'resumen_sistema': {},
    }

    # Resumen general
    s = SyncEstado.objects.filter(id=1).first()
    respuesta['resumen_sistema'] = {
        'total_correos': CorreoCopia.objects.count(),
        'total_perfiles': PerfilRemitente.objects.count(),
        'urgentes_pendientes': CorreoCopia.objects.filter(es_pendiente=True).count(),
    }

    # Perfiles relevantes
    perfiles_qs = PerfilRemitente.objects.all()
    if q:
        perfiles_qs = perfiles_qs.filter(
            Q(nombre__icontains=q) | Q(email__icontains=q) |
            Q(empresa__icontains=q) | Q(resumen_perfil__icontains=q)
        )
    if tipo:
        perfiles_qs = perfiles_qs.filter(tipo=tipo)
    for p in perfiles_qs.order_by('-total_correos')[:5]:
        respuesta['perfiles'].append(_serializar_perfil_completo(p))

    # Correos relevantes
    correos_qs = CorreoCopia.objects.select_related('remitente')
    if q:
        correos_qs = correos_qs.filter(
            Q(de__icontains=q) | Q(asunto__icontains=q) |
            Q(resumen__icontains=q) |
            Q(remitente__nombre__icontains=q) |
            Q(remitente__email__icontains=q)
        )
    if tema:
        correos_qs = correos_qs.filter(tema=tema)
    if solo_urgentes:
        correos_qs = correos_qs.filter(es_pendiente=True)
    for c in correos_qs.order_by('-fecha')[:15]:
        respuesta['correos_relevantes'].append(_serializar_correo(c))

    # Documentos legales relevantes
    if q:
        docs = DocumentoLegal.objects.filter(
            activo=True
        ).filter(
            Q(titulo__icontains=q) | Q(tags__icontains=q) |
            Q(contenido__icontains=q)
        )[:3]
        for d in docs:
            respuesta['documentos_legales'].append({
                'titulo': d.titulo,
                'tipo': d.tipo,
                'fragmento': d.contenido[:800] if d.contenido else d.descripcion,
            })

    return JsonResponse(respuesta)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _serializar_correo(c):
    return {
        'id': c.id,
        'de': c.de,
        'asunto': c.asunto,
        'fecha': str(c.fecha),
        'tema': c.tema,
        'tono': c.tono,
        'es_pendiente': c.es_pendiente,
        'resumen': c.resumen or c.cuerpo[:300],
        'tiene_adjuntos': c.tiene_adjuntos,
        'adjuntos': c.nombres_adjuntos,
        'remitente': {
            'email': c.remitente.email if c.remitente else '',
            'nombre': c.remitente.nombre if c.remitente else '',
            'tipo': c.remitente.tipo if c.remitente else '',
        } if c.remitente else None,
    }


def _serializar_perfil_resumido(p):
    return {
        'email': p.email,
        'nombre': p.nombre,
        'empresa': p.empresa,
        'tipo': p.tipo,
        'nivel_prioridad': p.nivel_prioridad,
        'total_correos': p.total_correos,
        'pendientes_activos': p.pendientes_activos,
        'tono_predominante': p.tono_predominante,
        'ultimo_contacto': str(p.ultimo_contacto),
        'resumen_perfil': p.resumen_perfil,
    }


def _serializar_perfil_completo(p):
    temas = {}
    try:
        temas = json.loads(p.temas_frecuentes) if p.temas_frecuentes else {}
    except Exception:
        pass
    return {
        **_serializar_perfil_resumido(p),
        'rut': p.rut,
        'dominio': p.dominio,
        'es_empresa': p.es_empresa,
        'frecuencia': p.frecuencia,
        'primer_contacto': str(p.primer_contacto),
        'temas_frecuentes': temas,
        'ultima_solicitud': p.ultima_solicitud,
    }