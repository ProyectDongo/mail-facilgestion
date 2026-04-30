import re
import json
import datetime

DOMINIO_INTERNO = 'micontable.cl'

TEMAS_KEYWORDS = {
    'f29':                 ['f29', 'iva', 'declaracion mensual', 'impuesto mensual', 'debito fiscal', 'credito fiscal'],
    'f22':                 ['f22', 'renta', 'declaracion anual', 'impuesto a la renta', 'operacion renta'],
    'ppm':                 ['ppm', 'pago provisional', 'pagos provisionales mensuales'],
    'sii':                 ['sii', 'servicio de impuestos', 'rut', 'timbre', 'folio', 'contribuyente', 'boleta electronica', 'factura electronica'],
    'tgr':                 ['tgr', 'tesoreria', 'tesorería', 'deuda fiscal', 'convenio pago'],
    'inicio_termino_giro': ['inicio de actividades', 'termino de giro', 'término de giro', 'giro comercial'],
    'contrato_trabajo':    ['contrato de trabajo', 'contrato laboral', 'anexo contrato', 'jornada laboral'],
    'finiquito':           ['finiquito', 'termino contrato', 'término contrato', 'desvinculacion', 'desvinculación'],
    'despido':             ['despido', 'carta aviso', 'carta de despido', 'necesidades empresa', 'articulo 161', 'articulo 159', 'articulo 160'],
    'liquidacion_sueldo':  ['liquidacion de sueldo', 'liquidación', 'sueldo bruto', 'sueldo liquido', 'remuneracion', 'gratificacion', 'bono'],
    'licencia_medica':     ['licencia medica', 'licencia médica', 'reposo', 'isapre', 'fonasa', 'subsidio enfermedad'],
    'vacaciones':          ['vacaciones', 'feriado legal', 'dias habiles', 'descanso anual', 'feriado progresivo'],
    'accidente_laboral':   ['accidente laboral', 'accidente del trabajo', 'mutual', 'achs', 'ist', 'mutual de seguridad', 'denuncia accidente'],
    'direccion_trabajo':   ['direccion del trabajo', 'dirección del trabajo', 'inspector del trabajo', 'mediacion laboral', 'denuncia laboral'],
    'constitucion':        ['constitucion de sociedad', 'constitución', 'sociedad limitada', 'spa', 'sociedad anonima', 'escritura de constitucion'],
    'modificacion':        ['modificacion de estatutos', 'modificación', 'reforma estatutos', 'cambio de razon social'],
    'poder_notarial':      ['poder notarial', 'escritura publica', 'notaria', 'notaría', 'protocolizacion'],
    'balance':             ['balance', 'estado financiero', 'estado de resultado', 'utilidad', 'perdida', 'patrimonio'],
    'libro_contable':      ['libro diario', 'libro mayor', 'libro de compras', 'libro de ventas'],
    'cuentas_cobrar':      ['cuentas por cobrar', 'deudores', 'mora', 'cobranza', 'factura pendiente'],
    'cuentas_pagar':       ['cuentas por pagar', 'proveedores', 'pago pendiente', 'vencimiento pago'],
    'factura':             ['factura', 'boleta', 'nota de venta', 'documento tributario', 'dte'],
    'nota_credito':        ['nota de credito', 'nota de débito', 'nota de debito', 'anulacion factura'],
    'certificado':         ['certificado', 'certificacion', 'constancia', 'acreditacion'],
    'declaracion_jurada':  ['declaracion jurada', 'declaración jurada', ' dj '],
    'tarea_urgente':       ['urgente', 'a la brevedad', 'lo antes posible', 'vence hoy', 'vence mañana', 'plazo vencido'],
    'consulta':            ['consulta', 'quisiera saber', 'me podria informar', 'podria indicarme', 'como se hace', 'cual es el procedimiento'],
    'coordinacion':        ['reunion', 'reunión', 'llamada', 'videollamada', 'nos juntamos', 'disponibilidad'],
    'confirmacion':        ['confirmado', 'recibido', 'queda confirmado', 'tome nota', 'enterado', 'ok listo'],
    'seguimiento':         ['seguimiento', 'recordatorio', 'quedamos pendientes', 'hay novedades', 'en que estado'],
    'notificacion_sii':    ['sii.cl', 'notificacion sii', 'cedible', 'acuse de recibo sii', 'no-reply@sii.cl'],
    'notificacion_banco':  ['banco', 'transferencia recibida', 'abono en cuenta', 'cargo en cuenta', 'estado de cuenta', 'cartola'],
    'notificacion_prevision': ['afp', 'cotizacion previsional', 'previred', 'fonasa', 'isapre cotizacion'],
    'spam':                ['unsubscribe', 'darse de baja', 'oferta exclusiva', 'gana dinero', 'click aqui', 'promocion especial'],
}

TONO_KEYWORDS = {
    'urgente':   ['urgente', 'urgencia', 'inmediato', 'a la brevedad', 'plazo vencido', 'vence hoy', 'critico', 'crítico'],
    'formal':    ['estimado', 'distinguido', 'cordialmente', 'atentamente', 'saludos cordiales', 'me dirijo', 'mediante la presente', 'de mi consideracion'],
    'informal':  ['hola', 'hey', 'buen dia', 'buenas', 'gracias', 'saludos', 'cómo estás', 'como estas', 'te escribo'],
    'tecnico':   ['servidor', 'api', 'sistema', 'base de datos', 'configuracion', 'version', 'proceso', 'modulo'],
}

DOMINIOS_PERSONALES = [
    'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
    'live.com', 'icloud.com', 'yahoo.es', 'hotmail.es'
]

DOMINIOS_PUBLICOS = [
    'sii.cl', 'dt.gob.cl', 'tgr.cl', 'previred.com',
    'achs.cl', 'ist.cl', 'mutual.cl', 'suseso.cl',
    'cmfchile.cl', 'bcn.cl', 'gob.cl', 'chile.cl'
]

# keywords que realmente indican pendiente — más estrictos
PENDIENTE_KEYWORDS = [
    'urgente', 'a la brevedad', 'lo antes posible',
    'plazo vencido', 'vence hoy', 'vence mañana',
    'necesito que envie', 'necesito que me envie',
    'favor enviar', 'por favor enviar', 'pendiente de envio',
    'estamos esperando', 'sin respuesta', 'no hemos recibido',
]

RUT_PATTERN = re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b')


def detectar_rut(texto: str) -> str:
    match = RUT_PATTERN.search(texto)
    return match.group(0) if match else ''


def detectar_tema(asunto: str, cuerpo: str) -> str:
    texto = (asunto + ' ' + cuerpo[:800]).lower()
    puntajes = {tema: 0 for tema in TEMAS_KEYWORDS}
    for tema, keywords in TEMAS_KEYWORDS.items():
        for kw in keywords:
            if kw in texto:
                puntajes[tema] += 1
    if puntajes.get('tarea_urgente', 0) > 0:
        return 'tarea_urgente'
    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else 'otro'


def detectar_tono(asunto: str, cuerpo: str) -> str:
    texto = (asunto + ' ' + cuerpo[:400]).lower()
    for kw in TONO_KEYWORDS['urgente']:
        if kw in texto:
            return 'urgente'
    puntajes = {tono: 0 for tono in TONO_KEYWORDS}
    for tono, keywords in TONO_KEYWORDS.items():
        for kw in keywords:
            if kw in texto:
                puntajes[tono] += 1
    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else 'desconocido'


def es_pendiente(asunto: str, cuerpo: str) -> bool:
    texto = (asunto + ' ' + cuerpo[:400]).lower()
    return any(p in texto for p in PENDIENTE_KEYWORDS)


def generar_resumen(asunto: str, cuerpo: str) -> str:
    texto = re.sub(r'\s+', ' ', cuerpo[:1000]).strip()
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    resumen = ' '.join(oraciones[:2])
    return resumen[:300] if resumen else asunto


def detectar_tipo_remitente(email: str, dominio: str) -> str:
    if dominio == DOMINIO_INTERNO:
        return 'interno'
    if dominio in DOMINIOS_PUBLICOS:
        return 'organismo_publico'
    if dominio in DOMINIOS_PERSONALES:
        return 'cliente'
    if dominio:
        return 'cliente'
    return 'desconocido'


def detectar_frecuencia(total_correos: int) -> str:
    if total_correos >= 100:
        return 'diaria'
    if total_correos >= 30:
        return 'semanal'
    if total_correos >= 5:
        return 'mensual'
    return 'esporadica'


def detectar_prioridad(total_correos: int, pendientes: int, tono: str) -> str:
    if tono == 'urgente' or pendientes > 10:
        return 'alta'
    if total_correos >= 50 or pendientes > 3:
        return 'media'
    return 'baja'


def actualizar_perfil(perfil, correos):
    if not correos:
        return

    tonos = [c.tono for c in correos if c.tono != 'desconocido']
    if tonos:
        perfil.tono_predominante = max(set(tonos), key=tonos.count)

    temas = [c.tema for c in correos if c.tema != 'otro']
    conteo = {}
    for t in temas:
        conteo[t] = conteo.get(t, 0) + 1
    perfil.temas_frecuentes = json.dumps(conteo, ensure_ascii=False)

    pendientes = sum(1 for c in correos if c.es_pendiente)
    perfil.pendientes_activos = pendientes
    perfil.frecuencia = detectar_frecuencia(perfil.total_correos)
    perfil.nivel_prioridad = detectar_prioridad(
        perfil.total_correos, pendientes, perfil.tono_predominante
    )

    ultimos = sorted(
        [c for c in correos if c.resumen],
        key=lambda x: x.fecha or datetime.datetime.min,
        reverse=True
    )
    if ultimos:
        perfil.ultima_solicitud = ultimos[0].resumen

    temas_str = ', '.join(list(conteo.keys())[:5]) if conteo else 'variados'
    perfil.resumen_perfil = (
        f"{perfil.nombre or perfil.email} — {perfil.tipo} — "
        f"{perfil.total_correos} correos — "
        f"tono: {perfil.tono_predominante} — "
        f"frecuencia: {perfil.frecuencia} — "
        f"temas: {temas_str} — "
        f"pendientes: {pendientes} — "
        f"prioridad: {perfil.nivel_prioridad}"
    )

    perfil.clasificado = True
    perfil.save()
