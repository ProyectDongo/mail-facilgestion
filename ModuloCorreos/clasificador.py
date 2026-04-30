import re
import json
import datetime

DOMINIO_INTERNO = 'micontable.cl'

# ─────────────────────────────────────────────
# KEYWORDS — solo frases específicas, no palabras sueltas genéricas
# Las keywords cortas que aparecen en firmas (iva, rut, sii) se
# reemplazaron por frases más específicas para evitar falsos positivos
# ─────────────────────────────────────────────
TEMAS_KEYWORDS = {
    # Tributario — frases específicas, no palabras sueltas
    'f29': [
        'formulario 29', 'f-29', 'declaracion de iva', 'declaracion iva',
        'impuesto al valor agregado', 'debito fiscal', 'credito fiscal',
        'declaracion mensual de impuestos', 'pago de iva',
    ],
    'f22': [
        'formulario 22', 'f-22', 'declaracion de renta', 'operacion renta',
        'impuesto a la renta anual', 'declaracion anual de impuestos',
        'renta anual', 'impuesto renta',
    ],
    'ppm': [
        'ppm', 'pago provisional mensual', 'pagos provisionales mensuales',
    ],
    'sii': [
        'servicio de impuestos internos', 'timbre electronico',
        'folio de factura', 'contribuyente de iva', 'inicio de actividades sii',
        'boleta electronica', 'factura electronica', 'notificacion sii',
        'resolucion sii', 'fiscalizacion sii',
    ],
    'tgr': [
        'tesoreria general', 'tgr', 'deuda fiscal', 'convenio de pago fiscal',
        'pago en tesoreria',
    ],
    'inicio_termino_giro': [
        'inicio de actividades', 'termino de giro', 'término de giro',
        'giro comercial',
    ],
    # Laboral
    'contrato_trabajo': [
        'contrato de trabajo', 'contrato laboral', 'creacion de contrato',
        'confeccion de contrato', 'anexo de contrato', 'renovacion de contrato',
        'jornada laboral', 'nuevo contrato',
    ],
    'finiquito': [
        'finiquito', 'confeccion de finiquito', 'creacion de finiquito',
        'termino de contrato', 'desvinculacion', 'desvinculación',
        'carta de finiquito',
    ],
    'despido': [
        'despido', 'carta de despido', 'carta aviso de despido',
        'necesidades de la empresa', 'articulo 161', 'articulo 159',
        'articulo 160', 'desahucio',
    ],
    'liquidacion_sueldo': [
        'liquidacion de sueldo', 'liquidacion de remuneraciones',
        'libro de remuneraciones', 'planilla de sueldos', 'sueldo bruto',
        'sueldo liquido', 'remuneraciones del mes', 'calculo de sueldo',
        'gratificacion legal', 'calculo remuneracion',
    ],
    'licencia_medica': [
        'licencia medica', 'licencia médica', 'dias de reposo',
        'subsidio de enfermedad', 'isapre licencia', 'fonasa licencia',
        'licencia laboral', 'baja medica',
    ],
    'vacaciones': [
        'vacaciones', 'feriado legal', 'dias habiles de vacaciones',
        'descanso anual', 'feriado progresivo', 'solicitud de vacaciones',
        'permiso de vacaciones',
    ],
    'accidente_laboral': [
        'accidente laboral', 'accidente del trabajo', 'mutual de seguridad',
        'achs', 'ist seguridad', 'denuncia de accidente',
        'accidente en faena', 'mutualidad',
    ],
    'direccion_trabajo': [
        'direccion del trabajo', 'dirección del trabajo',
        'inspector del trabajo', 'mediacion laboral',
        'denuncia laboral', 'dt.gob',
    ],
    # Societario
    'constitucion': [
        'constitucion de sociedad', 'constitucion de empresa',
        'escritura de constitucion', 'sociedad limitada', 'sociedad anonima',
        'spa constitucion', 'nueva sociedad',
    ],
    'modificacion': [
        'modificacion de estatutos', 'reforma de estatutos',
        'cambio de razon social', 'modificacion societaria',
    ],
    'poder_notarial': [
        'poder notarial', 'escritura publica', 'notaria',
        'protocolizacion', 'mandato notarial',
    ],
    # Contabilidad
    'balance': [
        'balance general', 'estado financiero', 'estado de resultados',
        'balance tributario', 'cierre contable', 'balance anual',
    ],
    'libro_contable': [
        'libro diario', 'libro mayor', 'libro de compras',
        'libro de ventas', 'libro contable',
    ],
    'cuentas_cobrar': [
        'cuentas por cobrar', 'facturas por cobrar', 'deudores',
        'factura pendiente de pago', 'mora en pago',
    ],
    'cuentas_pagar': [
        'cuentas por pagar', 'facturas por pagar',
        'pago pendiente a proveedor', 'vencimiento de pago',
    ],
    # Documental
    'factura': [
        'emitir factura', 'generar factura', 'solicitud de factura',
        'envio de factura', 'confeccion de factura', 'guia de despacho',
        'nota de venta', 'ceder factura', 'factura adjunta',
    ],
    'nota_credito': [
        'nota de credito', 'nota de débito', 'nota de debito',
        'anulacion de factura', 'devolucion factura',
    ],
    'certificado': [
        'certificado de', 'solicitud de certificado', 'certificado tributario',
        'certificado laboral', 'certificado de vigencia', 'f30', 'f30-1',
        'certificado de antecedentes', 'certificado de afiliacion',
    ],
    'declaracion_jurada': [
        'declaracion jurada', 'declaración jurada', 'jurada de',
    ],
    # Operacional
    'tarea_urgente': [
        'urgente', 'de urgencia', 'a la brevedad', 'lo antes posible',
        'vence hoy', 'vence mañana', 'plazo vencido', 'necesito urgente',
        'es urgente', 'necesitamos urgente',
    ],
    'consulta': [
        'quisiera consultar', 'tengo una consulta', 'me podria informar',
        'podria indicarme', 'como se hace', 'cual es el procedimiento',
        'tengo una duda', 'necesito saber',
    ],
    'coordinacion': [
        'agendar reunion', 'coordinar reunion', 'disponibilidad para',
        'nos juntamos', 'videollamada', 'llamada telefonica',
    ],
    'confirmacion': [
        'queda confirmado', 'confirmo recepcion', 'tome nota',
        'documentacion recibida', 'ok listo', 'recibido conforme',
    ],
    'seguimiento': [
        'seguimiento a', 'recordatorio de', 'quedamos pendientes',
        'hay novedades', 'en que estado esta', 'como va el tramite',
    ],
    # Automático
    'notificacion_sii': [
        'no-reply@sii.cl', 'notificacion de sii', 'cedible electronico',
        'acuse de recibo sii', 'sii.cl notifica',
    ],
    'notificacion_banco': [
        'transferencia recibida', 'abono en cuenta', 'cargo en cuenta',
        'estado de cuenta bancario', 'cartola bancaria', 'comprobante transferencia',
    ],
    'notificacion_prevision': [
        'cotizacion previsional', 'previred', 'pago afp',
        'isapre cotizacion', 'pago prevision',
    ],
    'spam': [
        'unsubscribe', 'darse de baja de esta lista', 'oferta exclusiva para',
        'gana dinero', 'haz clic aqui', 'promocion especial limitada',
    ],
}

# Peso extra para matches en el asunto (subject)
PESO_ASUNTO = 4
PESO_CUERPO = 1

TONO_KEYWORDS = {
    'urgente': [
        'urgente', 'urgencia', 'inmediato', 'a la brevedad',
        'plazo vencido', 'vence hoy', 'critico', 'crítico',
    ],
    'formal': [
        'estimado', 'distinguido', 'cordialmente', 'atentamente',
        'saludos cordiales', 'me dirijo a usted', 'mediante la presente',
        'de mi consideracion',
    ],
    'informal': [
        'hola', 'buen dia', 'buenas tardes', 'buenos dias',
        'gracias cynthia', 'gracias jose', 'saludos',
    ],
    'tecnico': [
        'servidor', 'base de datos', 'configuracion del sistema',
        'version del sistema',
    ],
}

DOMINIOS_PERSONALES = [
    'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
    'live.com', 'icloud.com', 'yahoo.es', 'hotmail.es',
]

DOMINIOS_PUBLICOS = [
    'sii.cl', 'dt.gob.cl', 'tgr.cl', 'previred.com',
    'achs.cl', 'ist.cl', 'mutual.cl', 'suseso.cl',
    'cmfchile.cl', 'bcn.cl', 'gob.cl', 'chile.cl',
]

# Pendientes — solo si aparecen en cuerpo REAL (no en texto citado)
# y son frases que expresan una SOLICITUD ACTIVA
PENDIENTE_KEYWORDS = [
    'urgente', 'de urgencia', 'a la brevedad',
    'lo antes posible', 'plazo vencido', 'vence hoy', 'vence mañana',
    'necesito urgente', 'necesitamos urgente',
    'favor enviar de manera urgente', 'favor realizar urgente',
    'sin respuesta aun', 'no hemos recibido respuesta',
    'estamos esperando respuesta', 'aun no recibimos',
    'solicito de forma urgente', 'solicito a usted de forma urgente',
]

RUT_PATTERN = re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b')


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def limpiar_cuerpo(cuerpo: str) -> str:
    """
    Elimina texto citado (líneas que empiezan con >) y firmas típicas.
    Deja solo el contenido nuevo del remitente.
    """
    lineas = cuerpo.splitlines()
    limpias = []
    for linea in lineas:
        stripped = linea.strip()
        # omitir líneas citadas
        if stripped.startswith('>'):
            continue
        # omitir líneas de firma típica
        if re.match(r'^(atte\.|atentamente|saludos,?|regards|--\s*$)', stripped, re.IGNORECASE):
            break
        # omitir líneas de encabezado de respuesta citada
        if re.match(r'^(de:|para:|enviado el:|from:|sent:|on .* wrote:)', stripped, re.IGNORECASE):
            break
        limpias.append(linea)
    return ' '.join(limpias)


def limpiar_nombre(nombre_raw: str, email_addr: str) -> str:
    """
    Limpia el nombre del remitente.
    Si el display name es igual al email o está vacío, retorna vacío
    para que se pueda completar más adelante.
    """
    nombre = nombre_raw.strip().strip('"').strip("'")
    # Si el nombre es igual al email, no sirve
    if nombre.lower() == email_addr.lower():
        return ''
    # Si tiene formato email dentro del nombre
    if '@' in nombre:
        return ''
    # Si es muy corto, probablemente no es un nombre real
    if len(nombre) < 3:
        return ''
    return nombre


def detectar_rut(texto: str) -> str:
    match = RUT_PATTERN.search(texto)
    return match.group(0) if match else ''


# ─────────────────────────────────────────────
# CLASIFICACIÓN
# ─────────────────────────────────────────────

def detectar_tema(asunto: str, cuerpo: str) -> str:
    """
    Clasifica dando más peso al asunto que al cuerpo.
    Usa solo cuerpo limpio (sin texto citado).
    """
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    asunto_l = asunto.lower()
    cuerpo_l = cuerpo_limpio[:600].lower()

    puntajes = {tema: 0 for tema in TEMAS_KEYWORDS}

    for tema, keywords in TEMAS_KEYWORDS.items():
        for kw in keywords:
            if kw in asunto_l:
                puntajes[tema] += PESO_ASUNTO
            if kw in cuerpo_l:
                puntajes[tema] += PESO_CUERPO

    # tarea_urgente tiene prioridad si aparece en el asunto
    if puntajes.get('tarea_urgente', 0) >= PESO_ASUNTO:
        return 'tarea_urgente'

    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else 'otro'


def detectar_tono(asunto: str, cuerpo: str) -> str:
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    texto = (asunto + ' ' + cuerpo_limpio[:300]).lower()

    # urgente tiene prioridad
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
    """
    Solo marca como pendiente si la keyword aparece en:
    1. El asunto, O
    2. Las primeras 300 palabras del cuerpo LIMPIO (sin citas)
    """
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    texto = (asunto + ' ' + cuerpo_limpio[:500]).lower()
    return any(p in texto for p in PENDIENTE_KEYWORDS)


def generar_resumen(asunto: str, cuerpo: str) -> str:
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    texto = re.sub(r'\s+', ' ', cuerpo_limpio[:800]).strip()
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    resumen = ' '.join(oraciones[:2])
    return resumen[:300] if resumen else asunto


# ─────────────────────────────────────────────
# PERFIL
# ─────────────────────────────────────────────

def detectar_tipo_remitente(email_addr: str, dominio: str) -> str:
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
        key=lambda x: x.fecha if x.fecha and x.fecha.tzinfo is None
                      else (x.fecha.replace(tzinfo=None) if x.fecha else datetime.datetime.min),
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