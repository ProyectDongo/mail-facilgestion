import re as _re
from datetime import timedelta
from django.utils import timezone
from ModuloCorreos.models import CorreoCopia, PerfilRemitente
from ModuloCorreos.clasificador import (
    detectar_tema, detectar_tono, generar_resumen,
    es_pendiente, actualizar_perfil, detectar_tipo_remitente,
    limpiar_nombre,
)

PREFIJOS_RE = _re.compile(
    r'^(re|rv|rr|fw|fwd|reenviado|respuesta|resp)[\s:\-]+',
    _re.IGNORECASE
)
LIMITE_PENDIENTE = timezone.now() - timedelta(days=30)
total_procesados = 0

while True:
    correos = list(CorreoCopia.objects.filter(clasificado=False).select_related('remitente')[:200])
    if not correos:
        break
    for correo in correos:
        try:
            asunto_limpio = PREFIJOS_RE.sub('', correo.asunto).strip()
            correo.tema = detectar_tema(asunto_limpio, correo.cuerpo)
            correo.tono = detectar_tono(asunto_limpio, correo.cuerpo)
            correo.resumen = generar_resumen(asunto_limpio, correo.cuerpo)
            es_reciente = (correo.fecha is None or correo.fecha >= LIMITE_PENDIENTE)
            correo.es_pendiente = es_reciente and es_pendiente(asunto_limpio, correo.cuerpo)
            correo.clasificado = True
            correo.save()
            total_procesados += 1
        except Exception as e:
            print(f'Error correo {correo.id}: {e}')
            correo.clasificado = True
            correo.save()

    pendientes = CorreoCopia.objects.filter(clasificado=False).count()
    print(f'Procesados: {total_procesados} — Pendientes: {pendientes}')

print(f'FINALIZADO. Total: {total_procesados}')
