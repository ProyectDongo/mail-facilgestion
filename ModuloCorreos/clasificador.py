import re
import json
import datetime

DOMINIO_INTERNO = 'micontable.cl'

# ─────────────────────────────────────────────
# KEYWORDS — versión expandida para lenguaje real de clientes
#
# CRITERIO: Los correos reales son cortos e informales.
# "adjunto liquidacion de marzo", "necesito el contrato de juan",
# "favor emitir factura" — el clasificador anterior los perdía todos.
#
# ESTRATEGIA:
#   - Keywords cortas que matchean lenguaje cotidiano
#   - Frases largas para contextos específicos
#   - Separamos keywords de ASUNTO (mayor peso) vs CUERPO
# ─────────────────────────────────────────────

TEMAS_KEYWORDS = {

    # ── TRIBUTARIO ─────────────────────────────────────────────────────

    'f29': [
        # Frases específicas
        'formulario 29', 'f-29', 'f 29',
        'declaracion de iva', 'declaracion iva', 'pago de iva', 'pago iva',
        'impuesto al valor agregado', 'debito fiscal', 'credito fiscal',
        'declaracion mensual de impuestos', 'declaracion mensual',
        # Cortas pero con contexto suficiente
        'propuesta f29', 'f29 del mes', 'f29 de',
        'iva del mes', 'iva de este mes', 'iva pendiente',
        'impuesto mensual',
    ],

    'f22': [
        'formulario 22', 'f-22', 'f 22',
        'declaracion de renta', 'operacion renta', 'renta anual',
        'impuesto a la renta', 'impuesto renta', 'declaracion anual',
        'renta de personas', 'renta de la empresa',
        'propuesta f22', 'f22 del año',
        'devolución de impuestos', 'devolucion de impuestos',
        'declaracion anual de impuestos',
    ],

    'ppm': [
        'ppm', 'pago provisional', 'pagos provisionales',
        'pago provisional mensual', 'pagos provisionales mensuales',
        'ppm del mes', 'ppm pendiente',
    ],

    'sii': [
        'servicio de impuestos internos',
        'timbre electronico', 'folio de factura', 'folios',
        'inicio de actividades sii', 'inicio de actividades en el sii',
        'boleta electronica', 'factura electronica',
        'notificacion sii', 'resolucion sii', 'fiscalizacion sii',
        'rut de la empresa', 'rut empresa', 'tramite en sii',
        'sii notifica', 'carta del sii', 'citacion sii',
        'contribuyente', 'registro de compras', 'registro de ventas',
        'clave tributaria', 'clave sii',
    ],

    'tgr': [
        'tesoreria general', 'tgr', 'deuda fiscal',
        'convenio de pago fiscal', 'pago en tesoreria',
        'pago a tesoreria', 'deuda tesoreria',
        'morosidad fiscal', 'cuota tesoreria',
    ],

    'inicio_termino_giro': [
        'inicio de actividades', 'inicio de giro',
        'termino de giro', 'término de giro', 'termino de actividades',
        'giro comercial', 'modificacion de giro', 'cambio de giro',
        'ampliar giro', 'eliminar giro',
    ],

    # ── LABORAL ────────────────────────────────────────────────────────

    'contrato_trabajo': [
        # Frases completas
        'contrato de trabajo', 'contrato laboral',
        'confeccion de contrato', 'creacion de contrato',
        'renovacion de contrato', 'anexo de contrato',
        'nuevo contrato', 'actualizar contrato',
        # Frases cortas — el 80% de los correos reales
        'el contrato de', 'un contrato para', 'el contrato para',
        'necesito contrato', 'necesito el contrato', 'me hace el contrato',
        'me puede hacer el contrato', 'favor hacer contrato',
        'contrato nuevo', 'contrato del trabajador',
        'firmar contrato', 'firma del contrato',
        'jornada laboral', 'jornada de trabajo',
        'modificar contrato', 'cambio en el contrato',
        'hacer el contrato', 'preparar contrato',
        'enviar contrato', 'adjunto contrato', 'te mando contrato',
        'contrato adjunto',
    ],

    'finiquito': [
        # Frases completas
        'finiquito', 'carta de finiquito', 'confeccion de finiquito',
        'creacion de finiquito', 'termino de contrato',
        'desvinculacion', 'desvinculación',
        # Cortas pero unívocas — "finiquito" sola es suficiente
        'el finiquito de', 'un finiquito para', 'hacer el finiquito',
        'me hace el finiquito', 'necesito el finiquito',
        'preparar finiquito', 'calcular finiquito',
        'firmar finiquito', 'firma del finiquito',
        'finiquito del trabajador', 'finiquito pendiente',
        'me puede hacer el finiquito',
    ],

    'renuncia': [
        'renuncia voluntaria', 'carta de renuncia',
        'renuncia del trabajador', 'trabajador renuncia',
        'proceso de renuncia', 'renuncia de',
        'carta renuncia', 'notificacion de renuncia',
    ],

    'despido': [
        'despido', 'carta de despido', 'carta aviso de despido',
        'necesidades de la empresa', 'articulo 161', 'articulo 159',
        'articulo 160', 'desahucio', 'despido justificado',
        'causal de despido', 'aviso de despido',
    ],

    'liquidacion_sueldo': [
        # Frases completas
        'liquidacion de sueldo', 'liquidacion de remuneraciones',
        'planilla de sueldos', 'libro de remuneraciones',
        'calculo de sueldo', 'calculo remuneracion',
        'gratificacion legal', 'sueldo bruto', 'sueldo liquido',
        # Cortas — muy comunes en correos reales
        'liquidacion de', 'las liquidaciones', 'liquidaciones de',
        'liquidacion del mes', 'liquidacion mensual',
        'la liquidacion de', 'adjunto liquidacion', 'liquidacion adjunta',
        'remuneraciones del mes', 'remuneracion de',
        'adjunto remuneracion', 'planilla de remuneraciones',
        'calculo de remuneracion', 'calculo de remuneraciones',
        'sueldos del mes', 'pago de sueldos', 'pago de remuneraciones',
        'proceso de remuneraciones',
    ],

    'licencia_medica': [
        'licencia medica', 'licencia médica',
        'dias de reposo', 'subsidio de enfermedad',
        'isapre licencia', 'fonasa licencia',
        'licencia laboral', 'baja medica', 'reposo medico',
        'la licencia de', 'una licencia', 'licencia del trabajador',
        'adjunto licencia', 'envio licencia', 'tramitar licencia',
        'licencia por enfermedad', 'licencia por accidente',
    ],

    'vacaciones': [
        'vacaciones', 'feriado legal', 'feriado progresivo',
        'dias habiles de vacaciones', 'descanso anual',
        'solicitud de vacaciones', 'permiso de vacaciones',
        'calculo de vacaciones', 'vacaciones del trabajador',
        'vacaciones pendientes', 'dias de vacaciones',
        'proporcional de vacaciones',
    ],

    'accidente_laboral': [
        'accidente laboral', 'accidente del trabajo', 'accidente de trabajo',
        'mutual de seguridad', 'achs', 'ist seguridad', 'ist chile',
        'denuncia de accidente', 'accidente en faena',
        'mutualidad', 'diat', 'protocolo de accidente',
    ],

    'direccion_trabajo': [
        'direccion del trabajo', 'dirección del trabajo',
        'inspector del trabajo', 'mediacion laboral',
        'denuncia laboral', 'dt.gob', 'tramite en direccion del trabajo',
        'inspectoria del trabajo', 'multa de la dt',
    ],

    # ── SOCIETARIO ────────────────────────────────────────────────────

    'constitucion': [
        'constitucion de sociedad', 'constitucion de empresa',
        'escritura de constitucion', 'sociedad limitada', 'sociedad anonima',
        'spa constitucion', 'nueva sociedad', 'crear sociedad',
        'crear empresa', 'formar empresa',
        'sociedad por acciones', 'eirl', 'empresa individual',
    ],

    'modificacion': [
        'modificacion de estatutos', 'reforma de estatutos',
        'cambio de razon social', 'modificacion societaria',
        'cambio de socios', 'aumento de capital', 'disminucion de capital',
        'modificar la sociedad',
    ],

    'poder_notarial': [
        'poder notarial', 'escritura publica', 'notaria',
        'protocolizacion', 'mandato notarial',
        'ir a la notaria', 'firma en notaria',
        'ante notario',
    ],

    # ── CONTABILIDAD ──────────────────────────────────────────────────

    'balance': [
        'balance general', 'estado financiero', 'estado de resultados',
        'balance tributario', 'cierre contable', 'balance anual',
        'estados financieros', 'balance de la empresa',
        'informe financiero', 'resultado del ejercicio',
        'cierre del año',
    ],

    'libro_contable': [
        'libro diario', 'libro mayor', 'libro de compras',
        'libro de ventas', 'libro contable', 'libros contables',
        'contabilidad del mes', 'registros contables',
        'asiento contable', 'centro de costos',
    ],

    'cuentas_cobrar': [
        'cuentas por cobrar', 'facturas por cobrar',
        'deudores', 'factura pendiente de pago',
        'mora en pago', 'cobranza', 'clientes morosos',
        'deuda pendiente',
    ],

    'cuentas_pagar': [
        'cuentas por pagar', 'facturas por pagar',
        'pago a proveedor', 'vencimiento de pago',
        'pago pendiente', 'proveedor pendiente',
    ],

    'rendicion': [
        'rendicion de gastos', 'rendición de gastos',
        'gastos del mes', 'boletas de gastos',
        'gastos de representacion', 'rendicion de caja',
        'caja chica', 'anticipo de gastos',
        'rendicion mensual',
    ],

    'comprobante': [
        'comprobante de pago', 'comprobante de transferencia',
        'comprobante de deposito', 'adjunto comprobante',
        'comprobante adjunto', 'te mando el comprobante',
        'envio comprobante', 'recibo de pago',
    ],

    # ── DOCUMENTAL ────────────────────────────────────────────────────

    'factura': [
        # Frases de solicitud
        'emitir factura', 'generar factura', 'solicitud de factura',
        'confeccion de factura', 'necesito factura', 'hacer la factura',
        'me puede emitir', 'favor emitir',
        # Frases de envío / recepción
        'envio de factura', 'factura adjunta', 'adjunto factura',
        'te mando la factura', 'les envio factura',
        'guia de despacho', 'nota de venta',
        # Frases de estado
        'factura pendiente', 'factura sin pagar',
        'factura vencida', 'ceder factura', 'cesion de factura',
        # Cortas pero suficientes en contexto contable
        'la factura de', 'una factura por', 'la factura por',
        'facturas del mes', 'factura numero',
        'factura n°', 'factura n.',
    ],

    'nota_credito': [
        'nota de credito', 'nota de débito', 'nota de debito',
        'anulacion de factura', 'devolucion factura',
        'nc de', 'nota credito',
    ],

    'certificado': [
        'certificado de', 'solicitud de certificado',
        'certificado tributario', 'certificado laboral',
        'certificado de vigencia', 'f30', 'f30-1',
        'certificado de antecedentes', 'certificado de afiliacion',
        'certificado de cotizaciones', 'certificado de deuda',
        'certificado de inicio de actividades',
        'certificado de situacion tributaria',
        'necesito certificado', 'solicitar certificado',
        'obtener certificado',
    ],

    'declaracion_jurada': [
        'declaracion jurada', 'declaración jurada',
        'jurada de', 'dj de', 'dj1887', 'dj1879',
        'declaracion jurada simple',
    ],

    'documento_trabajador': [
        'documento del trabajador', 'documentos del personal',
        'ficha del trabajador', 'carpeta del trabajador',
        'datos del trabajador', 'informacion del empleado',
        'registro del trabajador',
    ],

    # ── OPERACIONAL ───────────────────────────────────────────────────

    'tarea_urgente': [
        'urgente', 'de urgencia', 'a la brevedad',
        'lo antes posible', 'lo mas pronto posible', 'lo más pronto posible',
        'vence hoy', 'vence mañana', 'vence esta semana',
        'plazo vencido', 'plazo limite', 'plazo límite',
        'necesito urgente', 'necesitamos urgente',
        'favor urgente', 'es urgente', 'muy urgente',
        'solicito urgente', 'requiero urgente',
        'favor realizar urgente', 'favor enviar urgente',
        'sin respuesta aun', 'aun sin respuesta',
        'no hemos recibido', 'estamos esperando',
    ],

    'consulta': [
        'quisiera consultar', 'tengo una consulta', 'tengo una pregunta',
        'me podria informar', 'me podrían informar',
        'podria indicarme', 'podrías indicarme',
        'como se hace', 'cual es el procedimiento',
        'tengo una duda', 'necesito saber', 'necesito informacion',
        'me puede explicar', 'que documentos necesito',
        'cuanto cuesta', 'cuál es el plazo',
        'como funciona', 'hay alguna forma de',
    ],

    'coordinacion': [
        'agendar reunion', 'coordinar reunion', 'disponibilidad para',
        'nos juntamos', 'videollamada', 'llamada telefonica',
        'podemos hablar', 'podriamos juntarnos',
        'zoom', 'meet', 'teams', 'llamada',
        'cuando podemos', 'tiene disponibilidad',
        'agendar una llamada',
    ],

    'confirmacion': [
        'queda confirmado', 'confirmo recepcion', 'tome nota',
        'documentacion recibida', 'ok listo', 'recibido conforme',
        'recibido gracias', 'ok muchas gracias', 'perfecto gracias',
        'conforme', 'acusamos recibo', 'recepcion conforme',
        'muchas gracias, recibido',
    ],

    'seguimiento': [
        'seguimiento a', 'recordatorio de', 'quedamos pendientes',
        'hay novedades', 'en que estado esta', 'como va el tramite',
        'como va', 'alguna novedad', 'me puede actualizar',
        'reiterarle mi solicitud', 'reitero mi solicitud',
        'sigo esperando', 'aun no he recibido',
        'me pueden informar el estado',
    ],

    'solicitud_fondos': [
        'solicitud de fondos', 'solicito fondos',
        'transferencia de fondos', 'solicito transferencia',
        'necesito fondos', 'anticipo de honorarios',
        'honorarios pendientes', 'cobro de honorarios',
        'boleta de honorarios', 'emitir boleta de honorarios',
    ],

    # ── AUTOMÁTICOS ───────────────────────────────────────────────────

    'notificacion_sii': [
        'no-reply@sii.cl', 'notificacion de sii',
        'cedible electronico', 'acuse de recibo sii',
        'sii.cl notifica', 'sii informa',
        'notificacion electronica sii',
    ],

    'notificacion_banco': [
        'transferencia recibida', 'abono en cuenta',
        'cargo en cuenta', 'estado de cuenta bancario',
        'cartola bancaria', 'comprobante transferencia',
        'transaccion exitosa', 'pago realizado exitosamente',
        'banco estado', 'banco de chile', 'bci informa',
        'scotiabank', 'santander informa',
    ],

    'notificacion_prevision': [
        'cotizacion previsional', 'previred', 'pago afp',
        'isapre cotizacion', 'pago prevision',
        'cotizaciones del mes', 'pago de cotizaciones',
        'afp informa', 'isapre informa',
    ],

    'spam': [
        'unsubscribe', 'darse de baja de esta lista',
        'oferta exclusiva para', 'gana dinero', 'haz clic aqui',
        'promocion especial limitada', 'precio especial',
        'click here to unsubscribe', 'this is a promotional',
    ],
}

# Peso extra para matches en el asunto
PESO_ASUNTO = 5
PESO_CUERPO = 1

# Keywords que SOLO se evalúan en el asunto (evitan falsos positivos en cuerpo)
# por ser términos muy cortos o ambiguos
SOLO_ASUNTO_KEYWORDS: dict[str, list[str]] = {
    'liquidacion_sueldo': ['liquidacion', 'remuneracion', 'remuneraciones'],
    'contrato_trabajo':   ['contrato'],
    'finiquito':          [],   # "finiquito" es suficientemente específica
    'factura':            ['factura', 'facturas'],
    'vacaciones':         ['vacaciones'],
    'licencia_medica':    ['licencia'],
    'certificado':        ['certificado'],
    'f29':                ['iva'],
    'tarea_urgente':      [],
}

TONO_KEYWORDS = {
    'urgente': [
        'urgente', 'urgencia', 'inmediato', 'a la brevedad',
        'plazo vencido', 'vence hoy', 'critico', 'crítico',
    ],
    'formal': [
        'estimado', 'distinguido', 'cordialmente', 'atentamente',
        'saludos cordiales', 'me dirijo a usted', 'mediante la presente',
        'de mi consideracion', 'de mi más alta consideración',
    ],
    'informal': [
        'hola', 'buen dia', 'buenos dias', 'buenas tardes',
        'buenas!', 'buenas,', 'gracias', 'saludos',
        'espero que estés bien', 'espero que este bien',
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

PENDIENTE_KEYWORDS = [
    'urgente', 'de urgencia', 'a la brevedad',
    'lo antes posible', 'lo más pronto posible', 'lo mas pronto posible',
    'vence hoy', 'vence mañana', 'plazo vencido',
    'necesito urgente', 'necesitamos urgente',
    'favor enviar de manera urgente', 'favor realizar urgente',
    'sin respuesta aun', 'aun sin respuesta',
    'no hemos recibido respuesta', 'estamos esperando respuesta',
    'aun no recibimos', 'sigo esperando',
    'solicito de forma urgente', 'solicito a usted de forma urgente',
    'reitero mi solicitud', 'reiterarle mi solicitud',
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
        if stripped.startswith('>'):
            continue
        if re.match(r'^(atte\.|atentamente|saludos,?|regards|--\s*$)', stripped, re.IGNORECASE):
            break
        if re.match(r'^(de:|para:|enviado el:|from:|sent:|on .* wrote:)', stripped, re.IGNORECASE):
            break
        limpias.append(linea)
    return ' '.join(limpias)


def limpiar_nombre(nombre_raw: str, email_addr: str) -> str:
    nombre = nombre_raw.strip().strip('"').strip("'")
    if nombre.lower() == email_addr.lower():
        return ''
    if '@' in nombre:
        return ''
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
    Aplica keywords cortas solo en el asunto para evitar falsos positivos.
    """
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    asunto_l = asunto.lower()
    cuerpo_l = cuerpo_limpio[:800].lower()

    puntajes: dict[str, float] = {tema: 0 for tema in TEMAS_KEYWORDS}

    # Keywords principales en asunto y cuerpo
    for tema, keywords in TEMAS_KEYWORDS.items():
        for kw in keywords:
            if kw in asunto_l:
                puntajes[tema] += PESO_ASUNTO
            elif kw in cuerpo_l:
                puntajes[tema] += PESO_CUERPO

    # Keywords cortas solo en asunto (más confiables ahí)
    for tema, keywords in SOLO_ASUNTO_KEYWORDS.items():
        for kw in keywords:
            if kw in asunto_l:
                puntajes[tema] += PESO_ASUNTO

    # tarea_urgente tiene prioridad si aparece en el asunto
    if puntajes.get('tarea_urgente', 0) >= PESO_ASUNTO:
        return 'tarea_urgente'

    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else 'otro'


def detectar_tono(asunto: str, cuerpo: str) -> str:
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    texto = (asunto + ' ' + cuerpo_limpio[:400]).lower()

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
    2. Las primeras 500 palabras del cuerpo LIMPIO (sin citas)
    """
    cuerpo_limpio = limpiar_cuerpo(cuerpo)
    texto = (asunto + ' ' + cuerpo_limpio[:600]).lower()
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