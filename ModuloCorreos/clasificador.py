"""
clasificador.py — Motor de clasificación de correos para empresa contable.
Optimizado para lectura rápida por IAs: cada función retorna strings simples,
los patrones están ordenados por frecuencia para mayor velocidad.
"""

import re
import json
import datetime

# ─────────────────────────────────────────────────────────────
# DOMINIOS
# ─────────────────────────────────────────────────────────────

DOMINIO_INTERNO = 'micontable.cl'

DOMINIOS_PERSONALES = {
    'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
    'live.com', 'icloud.com', 'yahoo.es', 'hotmail.es',
    'gmail.cl', 'hotmail.cl',
}

DOMINIOS_PUBLICOS = {
    'sii.cl', 'dt.gob.cl', 'tgr.cl', 'previred.com',
    'achs.cl', 'ist.cl', 'mutual.cl', 'suseso.cl',
    'cmfchile.cl', 'bcn.cl', 'gob.cl', 'chile.cl',
    'caja-losandes.cl', 'consalud.cl', 'banmedica.cl',
    'nuevamasvida.cl', 'isapre.cl', 'fonasa.cl',
    'afp.cl', 'provida.cl', 'habitacoop.cl',
}

# ─────────────────────────────────────────────────────────────
# KEYWORDS POR TEMA
# Orden: los más frecuentes primero para mayor velocidad
# ─────────────────────────────────────────────────────────────

TEMAS_KEYWORDS = {

    # ── LABORAL (los más frecuentes en esta empresa) ──────────

    'contrato_trabajo': [
        # Contratos genéricos
        'contrato de trabajo', 'contrato laboral', 'contrato trabajador',
        'contrato tipo', 'contrato indefinido', 'contrato plazo fijo',
        'contrato olivia', 'contrato sandra', 'contrato valentina',
        'contrato jessica', 'contrato de arriendo',
        # Solicitudes de creación
        'solicitud de contrato', 'solicitud de creacion de contrato',
        'solicitud de extension de contrato', 'solicitud de contratacion',
        'generar contrato', 'creacion de contrato', 'contratacion y anexos',
        'contratacion ', 'solicitud contrato mdo',
        # Anexos
        'anexo contrato', 'anexo contraro', 'anexo de renovacion',
        'renovacion contrato', 'anexo reajuste', 'anexo horario',
        'anexo firmado', 'anexo indefinido', 'anexo salvador',
        'anexo fernando', 'anexo de contrato', 'anexo paula',
        'anexo continuidad', 'solicitud de anexo', 'creacion de anexo',
        'informacion para contrato', 'informacion para contrato y anexo',
        'anexos', 're: solicitud anexo',
        # Condiciones laborales
        'horario de trabajo', 'jornada laboral', 'cambio de jornada',
        'cambio jornada', 'resolucion jornada', 'resolución jornada',
        'jornada 7x7', 'jornada 4x3', 'jornada 10x5',
        'documento cambio de dia', 'documento cambio de día',
        # Reajustes y modificaciones
        'reajuste sueldo', 'reajuste de cargo', 'reajuste de sueldo',
        'aumento de sueldo', 'modificacion de liquidacion',
        'revocacion de descuento', 'cambio de cargo',
        # Parámetros y roles
        'parametros', 'solicitud de parametros', 'solicitud de rol',
        # Reglamento
        'reglamento interno', 'reglamento de orden',
        'clausulas de proteccion', 'clausulas de protección',
        # Personal específico
        'personal ductos', 'personal nuevo',
    ],

    'liquidacion_sueldo': [
        # Liquidaciones
        'liquidacion de sueldo', 'liquidación de sueldo',
        'liquidacion sueldo', 'liquidaciones de sueldo',
        'liquidaciones sueldos', 'liquidaciones de mayo',
        'liquidaciones enero', 'liquidaciones febrero',
        'liquidaciones maritza', 'liquidacion juan',
        'liquidacion julio', 'liquidacion corregida',
        'liquidacion y anexo', 'fwd: liquidacion',
        'modif. liquidacion', 'modificacion liquidacion',
        'planilla de liquidaciones', 'solicitud de liquidacion',
        # Remuneraciones y sueldos
        'sueldo bruto', 'sueldo liquido', 'remuneracion',
        'gratificacion', 'informacion para liquidacion',
        'llenado de planilla', 'planilla de costos',
        # Nóminas y estados
        'nomina', 'nómina', 'estado de pago',
        'pagos mensuales', 'pago pensiones',
        'imposiciones', 'pago imposiciones',
        'imposiciones julio', 'imposiciones noviembre',
        # Libros contables de ventas (frecuentes en esta empresa)
        'libro venta', 'libro ventas', 'libro de venta',
        'libros de compra ventas', 'verónica calle libro',
        'libro ventas nov', 'libro ventas octubre',
        'libro ventas marzo', 'ventas abril', 'ventas enero',
        'ventas julio', 'ventas septiembre', 'ventas noviembre',
        'ventas octubre', 'ventas mes', 'compras enero',
        # APV y otros beneficios
        'liquidaciones apv', 'bono',
        # Anticipos
        'anticipos', 'anticipos mes',
    ],

    'accidente_laboral': [
        'accidente laboral', 'accidente del trabajo',
        'mutual de seguridad', 'denuncia accidente',
        'mutual', 'achs', 'ist',
        'inasistencia', 'trabajador no da aviso',
        'falla en trabajo',
    ],

    'licencia_medica': [
        'licencia medica', 'licencia médica', 'licencia',
        'reposo medico', 'subsidio enfermedad',
        'aviso importante cotizaciones isapre',
        'isapre consalud', 'cotizaciones isapre',
        'formulario isapre', 'inscripcion isapre',
        'permiso parental', 'post natal',
        'permiso sin goce de sueldo',
    ],

    'vacaciones': [
        'vacaciones', 'feriado legal', 'dias habiles',
        'descanso anual', 'feriado progresivo',
        'permiso vacaciones', 'vacacion luis',
        'dia de permiso', 'día de permiso',
        'permisos',
    ],

    'finiquito': [
        'finiquito', 'termino contrato', 'término contrato',
        'desvinculacion', 'desvinculación',
        'termino de servicio', 'término de servicio',
        'término de obra', 'termino de obra',
        'cartas de salida', 'solicitud de cartas de salida',
    ],

    'renuncia': [
        'renuncia', 'renuncia voluntaria', 'carta de renuncia',
        'solicitud de reincorporacion', 'reincorporacion',
    ],

    'despido': [
        'despido', 'carta de despido',
        'necesidades empresa', 'articulo 161', 'articulo 159',
        'articulo 160', 'carta de aviso', 'cartas de aviso',
        'solicitud de carta de aviso', 'solicitud de cartas de aviso',
        'personal 5 dias', 'carta por falla', 'falla reiterada',
        'carta de amonestacion', 'amonestacion', 'carta amonesta',
        'aviso por termino',
    ],

    'direccion_trabajo': [
        'direccion del trabajo', 'dirección del trabajo',
        'inspector del trabajo', 'mediacion laboral',
        'denuncia laboral', 'auditoria laboral',
        'auditorias laborales', 'envio de documentacion auditoria',
        'documentacion de auditoria', 'informacion auditoria',
        'notificacion reclamo', 'notificación de reclamo',
        'notifica reclamo', 'ingreso de requerimiento',
        'proceso de licitacion', 'licitacion kinross',
        'carta notificacion decreto', 'decreto',
        'demanda', 'causa romero', 'tramites rel',
        'empleador verifica', 'relacion laboral',
        'ord. n°', 'carta litot',
    ],

    # ── TRIBUTARIO ────────────────────────────────────────────

    'f29': [
        'f29', 'declaracion mensual', 'impuesto mensual',
        'debito fiscal', 'credito fiscal',
        'modificacion f29', 'modifcacion f29',
        'declaracion iva', 'iva mensual',
        'lre - declaración', 'lre declaracion',
        'presenta observaciones', 'invitacion renta at',
    ],

    'f22': [
        'f22', 'declaracion anual', 'impuesto a la renta',
        'operacion renta', 'renta anual',
        'fwd: operación renta', 'operación renta at2025',
        'at2025', 'at2024',
    ],

    'sii': [
        'sii', 'servicio de impuestos', 'timbre', 'folio',
        'contribuyente', 'boleta electronica', 'factura electronica',
        'sii.cl', 'cedible', 'acuse de recibo sii',
        'f-30', 'f.30', 'f30', 'creacion de obra',
        'carpeta tributaria', 'solicitar carpeta tributaria',
        'pasos para solicitud de carpeta',
        'correo notificaciones citaciones', 'validacion de documento',
        'recupera clave', 'clave sii', 'intranet sii',
    ],

    'tgr': [
        'tgr', 'tesoreria', 'tesorería', 'deuda fiscal',
        'convenio pago tgr', 'tesoreria general',
        'gc impagos',
    ],

    'ppm': ['ppm', 'pago provisional', 'pagos provisionales mensuales'],

    'inicio_termino_giro': [
        'inicio de actividades', 'termino de giro',
        'término de giro', 'giro comercial',
    ],

    # ── CONTABILIDAD ──────────────────────────────────────────

    'balance': [
        'balance', 'estado financiero', 'estado de resultado',
        'utilidad', 'perdida', 'patrimonio',
        'balance noviembre', 'balance octubre', 'balance mes',
        'cierre año', 'proyeccion cierre año', 'cierre contable',
        'rv: balance', 'balance mdh',
    ],

    'libro_contable': [
        'libro diario', 'libro mayor',
        'libro de compras', 'libro de ventas',
        'libros de compra', 'contabilidad general',
        'auxiliar cta clientes',
    ],

    'cuentas_cobrar': [
        'cuentas por cobrar', 'deudores', 'mora cobranza',
        'factura pendiente', 'edp tbp', 'estado de avance',
    ],

    'cuentas_pagar': [
        'cuentas por pagar', 'proveedores',
        'pago pendiente', 'vencimiento pago',
        'gasto comun', 'gasto común', 'luminaria y gas',
    ],

    'rendicion': [
        'rendicion', 'rendición', 'rendicion de gastos',
        'rendicion premios', 'rendicion fiesta',
        'reembolso flores', 'reembolso',
        'gastos aniversario', 'gastos 2024',
        'caja chica', 'rv: caja chica',
        'solicitud de incorporacion a planilla de gastos',
        'planilla de gastos',
    ],

    'comprobante': [
        'comprobante', 'comprobantes', 'voucher',
        'pago beneficiario', 'notificacion pago beneficiario',
        'correos electronicos conformidad',
    ],

    # ── SOCIETARIO ────────────────────────────────────────────

    'constitucion': [
        'constitucion de sociedad', 'constitución de sociedad',
        'sociedad limitada', 'spa', 'sociedad anonima',
        'escritura de constitucion', 'informacion de empresa',
        'solicitud de requerimientos para abrir cuenta',
        'apertura linea de credito', 'apertura de cuenta',
        'creacion de destinatario pyme', 'destinatario pyme',
        'cambio de datos de representante legal',
        'redelcom',
    ],

    'modificacion': [
        'modificacion de estatutos', 'modificación de estatutos',
        'modificacion al estatuto', 'reforma estatutos',
        'cambio de razon social',
    ],

    'poder_notarial': [
        'poder notarial', 'escritura publica',
        'notaria', 'notaría', 'protocolizacion',
        'firma formulario', 'autorizacion de firmas',
        'autorización de firmas',
    ],

    # ── DOCUMENTAL ────────────────────────────────────────────

    'factura': [
        'factura', 'boleta', 'nota de venta',
        'documento tributario', 'dte',
        'solicitud de boleta', 'solicitud de guia',
        'guia de despacho', 'detalle boletas',
        'boletas de garantia', 'anular guia',
        'orden de compra', 'cotizacion', 'factoring',
        'envio cotizacion', 'boceto solicitado',
        'planilla de costos productivos',
        'contrato leasing',
    ],

    'nota_credito': [
        'nota de credito', 'nota de débito', 'nota de debito',
        'anulacion factura',
    ],

    'certificado': [
        'certificado', 'certificacion', 'constancia',
        'acreditacion', 'vbo', 'vºbº',
        'firma cuota', 'cuota regional',
        'nomina colegiados', 'nómina colegiados',
        'pago bienestar', 'doctos navidad',
        'cert, correo',
    ],

    'declaracion_jurada': [
        'declaracion jurada', 'declaración jurada', ' dj ',
        'nomina de retenciones', 'nómina de retenciones',
        'credito social', 'caja los andes',
    ],

    'documento_trabajador': [
        'documentos trabajador', 'documentacion trabajador',
        'documento trabajador', 'documentos juan',
        'documentos personal', 'carpeta trabajador',
        'solicitud de documentacion',
        'solicitud de documentos', 'doumentos solicitados',
        'envio de documentacion',
        'termino de servicios de contabilidad',
        'datos jose muñoz', 'datos trabajador',
        'documento de ana', 'graciela alvarado',
        'cv lic', 'cv patricia', 'fotocopias', 'fotocopia',
        'lm marcelo',
    ],

    # ── PREVISIÓN Y BANCO ─────────────────────────────────────

    'notificacion_prevision': [
        'afp', 'cotizacion previsional', 'previred',
        'cotizaciones de salud', 'pago cotizaciones',
        'trabajadores no vigentes', 'nueva masvida',
        'isapre cotizacion', 'fonasa',
        'deuda por cotizaciones', 'cotizaciones de seguridad social',
        'aviso para regularizacion', 'mora presunta',
        'nueva cotizacion de cargo', 'cargo del empleador',
        'webinar cotizacion', 'prestamo blando',
        'solicitud de mi clave afc',
    ],

    'notificacion_banco': [
        'transferencia recibida', 'abono en cuenta',
        'cargo en cuenta', 'estado de cuenta',
        'cartola', 'cartola bci',
        'codigo de creacion nuevo beneficiario',
    ],

    'solicitud_fondos': [
        'solicitud de fondos', 'transferencias',
        'pago rifa', 'pago bienestar', 'pago fiestas patrias',
        'anticipos', 'rifa', 'caja chica',
        'pago bienestar y cuota regional',
        'solicita fondos para cancelar',
        'apertura linea de credito',
    ],

    # ── OPERACIONAL ───────────────────────────────────────────

    'tarea_urgente': [
        'urgente', 'a la brevedad', 'lo antes posible',
        'vence hoy', 'vence mañana', 'plazo vencido',
        'necesito que envie', 'favor enviar',
    ],

    'consulta': [
        'consulta', 'quisiera saber', 'me podria informar',
        'podria indicarme', 'como se hace',
        'cual es el procedimiento',
        'solicitud de informacion', 'informacion solicitada',
        'informacion para', 'informavion',
        're: solicitud de información',
    ],

    'coordinacion': [
        'reunion', 'reunión', 'llamada', 'videollamada',
        'nos juntamos', 'disponibilidad',
        'capacitacion', 'invitacion a capacitacion',
        'desayuno exclusivo', 'compra de camioneta',
        'cursos',
    ],

    'confirmacion': [
        'confirmado', 'recibido', 'queda confirmado',
        'tome nota', 'enterado', 'ok listo',
        'documento firmado electronicamente',
        'rv: documento firmado',
    ],

    'seguimiento': [
        'seguimiento', 'recordatorio', 'quedamos pendientes',
        'hay novedades', 'en que estado',
        'rv: informacion solicitada',
    ],

    'notificacion_sii': [
        'notificacion sii', 'no-reply@sii.cl',
        'acuse de recibo sii', 'correo notificaciones citaciones',
        'correo verificado',
    ],

    # ── SPAM / RUIDO ──────────────────────────────────────────

    'spam': [
        'unsubscribe', 'darse de baja', 'oferta exclusiva',
        'gana dinero', 'click aqui', 'promocion especial',
        'message delivery failure', 'mail delivery system',
        'mail delivery failed', 'undeliverable',
        'corona de caridad', 'tu opinion vale',
        'smart tv', 'tiko tiki', 'parrilla',
        'rrhh defontana', 'comunidad de edificio',
        'cosmocentro plaza real', 'primer inicio de sesion',
        'mensaje de prueba', 'microsoft outlook prueba',
        'e&s',
    ],
}

# ─────────────────────────────────────────────────────────────
# TONOS
# ─────────────────────────────────────────────────────────────

TONO_KEYWORDS = {
    'urgente': [
        'urgente', 'urgencia', 'inmediato', 'a la brevedad',
        'plazo vencido', 'vence hoy', 'critico', 'crítico',
        'necesito hoy', 'lo antes posible',
    ],
    'formal': [
        'estimado', 'distinguido', 'cordialmente', 'atentamente',
        'saludos cordiales', 'me dirijo', 'mediante la presente',
        'de mi consideracion', 'de mi consideración',
        'me permito', 'adjunto encontrará',
    ],
    'informal': [
        'hola', 'hey', 'buen dia', 'buenas', 'gracias',
        'saludos', 'cómo estás', 'como estas', 'te escribo',
        'wena', 'cualquier cosa', 'buen día',
    ],
    'tecnico': [
        'servidor', 'api', 'sistema', 'base de datos',
        'configuracion', 'version', 'proceso', 'modulo',
    ],
}

# ─────────────────────────────────────────────────────────────
# PENDIENTES — keywords estrictas para no sobredimensionar
# ─────────────────────────────────────────────────────────────

PENDIENTE_KEYWORDS = [
    'urgente', 'a la brevedad', 'lo antes posible',
    'plazo vencido', 'vence hoy', 'vence mañana',
    'necesito que envie', 'necesito que me envie',
    'favor enviar', 'por favor enviar', 'pendiente de envio',
    'estamos esperando', 'sin respuesta', 'no hemos recibido',
    'mora presunta', 'aviso para regularizacion',
    'deuda por cotizaciones',
]

# ─────────────────────────────────────────────────────────────
# REGEX
# ─────────────────────────────────────────────────────────────

PREFIJOS_RE = re.compile(
    r'^(re|rv|rr|fw|fwd|reenviado|respuesta|resp|fwd:|re:|rv:)[\s:\-]*',
    re.IGNORECASE
)

RUT_PATTERN = re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b')

PALABRAS_NO_NOMBRE = {
    'mr', 'mrs', 'ms', 'dr', 'ing', 'lic', 'don', 'doña',
    'señor', 'señora', 'sr', 'sra', 'att', 'de', 'del',
    'via', 'on', 'behalf', 'of', 'per', 'para', 'por',
    'noreply', 'no-reply', 'donotreply', 'info', 'contacto',
    'ventas', 'soporte', 'admin', 'administracion',
    'notificaciones', 'alertas', 'sistema', 'automatico',
}

# ─────────────────────────────────────────────────────────────
# FUNCIONES PÚBLICAS
# ─────────────────────────────────────────────────────────────

def limpiar_nombre(nombre_raw: str, email_addr: str) -> str:
    if not nombre_raw or nombre_raw.strip() == email_addr.strip():
        return ''
    nombre = nombre_raw.strip().strip('"\'<>').strip()
    if not nombre or '@' in nombre:
        return ''
    palabras = nombre.lower().split()
    if all(p in PALABRAS_NO_NOMBRE for p in palabras):
        return ''
    if len(nombre) < 3:
        return ''
    return nombre


def detectar_rut(texto: str) -> str:
    match = RUT_PATTERN.search(texto)
    return match.group(0) if match else ''


def limpiar_asunto(asunto: str) -> str:
    return PREFIJOS_RE.sub('', asunto).strip()


def detectar_tema(asunto: str, cuerpo: str) -> str:
    """
    Detecta el tema principal del correo.
    Retorna string simple — óptimo para consultas de IA.
    """
    asunto_limpio = limpiar_asunto(asunto)
    texto = (asunto_limpio + ' ' + cuerpo[:800]).lower()

    # Urgente tiene prioridad absoluta
    if any(kw in texto for kw in TEMAS_KEYWORDS['tarea_urgente']):
        return 'tarea_urgente'

    # Spam tiene segunda prioridad (evita falsos positivos)
    if any(kw in texto for kw in TEMAS_KEYWORDS['spam']):
        return 'spam'

    puntajes = {}
    for tema, keywords in TEMAS_KEYWORDS.items():
        if tema in ('tarea_urgente', 'spam'):
            continue
        puntaje = sum(1 for kw in keywords if kw in texto)
        if puntaje > 0:
            puntajes[tema] = puntaje

    if not puntajes:
        return 'otro'

    return max(puntajes, key=puntajes.get)


def detectar_tono(asunto: str, cuerpo: str) -> str:
    texto = (asunto + ' ' + cuerpo[:400]).lower()
    for kw in TONO_KEYWORDS['urgente']:
        if kw in texto:
            return 'urgente'
    puntajes = {
        tono: sum(1 for kw in kws if kw in texto)
        for tono, kws in TONO_KEYWORDS.items()
    }
    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else 'desconocido'


def es_pendiente(asunto: str, cuerpo: str) -> bool:
    texto = (asunto + ' ' + cuerpo[:400]).lower()
    return any(p in texto for p in PENDIENTE_KEYWORDS)


def generar_resumen(asunto: str, cuerpo: str) -> str:
    """Genera resumen limpio de 2 oraciones para lectura rápida de IA."""
    texto = re.sub(r'\s+', ' ', cuerpo[:1000]).strip()
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    resumen = ' '.join(oraciones[:2])
    return resumen[:300] if resumen else asunto


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


def calcular_patron_dias(correos) -> dict:
    dias = {}
    nombres_dias = {
        0: 'lunes', 1: 'martes', 2: 'miercoles',
        3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo',
    }
    for c in correos:
        if c.fecha:
            try:
                dia = nombres_dias[c.fecha.weekday()]
                dias[dia] = dias.get(dia, 0) + 1
            except Exception:
                pass
    return dias


def calcular_patron_dias_mes(correos) -> dict:
    dias = {}
    for c in correos:
        if c.fecha:
            try:
                dia = str(c.fecha.day)
                dias[dia] = dias.get(dia, 0) + 1
            except Exception:
                pass
    return dias


def calcular_adjuntos(correos) -> tuple:
    tipos = {}
    total = len(correos)
    con_adjuntos = 0
    for c in correos:
        if c.tiene_adjuntos:
            con_adjuntos += 1
            for nombre in c.nombres_adjuntos.split(','):
                nombre = nombre.strip().lower()
                if '.' in nombre:
                    ext = nombre.rsplit('.', 1)[-1].strip()
                    if ext and len(ext) <= 5:
                        tipos[ext] = tipos.get(ext, 0) + 1
    tasa = round(con_adjuntos / total, 2) if total > 0 else 0.0
    return tipos, tasa


def generar_contexto_ia(perfil, temas: dict, patron_semana: dict,
                         tasa_adj: float, pendientes: int) -> str:
    """
    Genera texto de contexto optimizado para que la IA entienda
    rápidamente quién es este cliente y qué necesita.
    """
    dia_frecuente = max(patron_semana, key=patron_semana.get) if patron_semana else ''
    temas_top = ', '.join(
        f"{k}({v})" for k, v in
        sorted(temas.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    ctx = (
        f"CLIENTE: {perfil.nombre or perfil.email} | "
        f"TIPO: {perfil.tipo} | "
        f"EMPRESA: {perfil.empresa or perfil.dominio} | "
        f"CORREOS: {perfil.total_correos} | "
        f"TONO: {perfil.tono_predominante} | "
        f"FRECUENCIA: {perfil.frecuencia} | "
        f"TEMAS: {temas_top} | "
        f"PENDIENTES: {pendientes} | "
        f"PRIORIDAD: {perfil.nivel_prioridad}"
    )
    if dia_frecuente:
        ctx += f" | ESCRIBE_LOS: {dia_frecuente}"
    if tasa_adj > 0.3:
        ctx += f" | ADJUNTA_DOCS: {int(tasa_adj*100)}%"
    if perfil.ultima_solicitud:
        ctx += f" | ULTIMA_SOLICITUD: {perfil.ultima_solicitud[:100]}"
    return ctx


def actualizar_perfil(perfil, correos):
    """
    Recalcula y guarda todos los campos del perfil basado en sus correos.
    Se llama automáticamente tras clasificar correos nuevos.
    """
    if not correos:
        return

    # Tono predominante
    tonos = [c.tono for c in correos if c.tono != 'desconocido']
    if tonos:
        perfil.tono_predominante = max(set(tonos), key=tonos.count)

    # Temas
    temas_lista = [c.tema for c in correos if c.tema not in ('otro', 'spam')]
    conteo_temas = {}
    for t in temas_lista:
        conteo_temas[t] = conteo_temas.get(t, 0) + 1
    perfil.temas_frecuentes = json.dumps(conteo_temas, ensure_ascii=False)

    # Pendientes
    pendientes = sum(1 for c in correos if c.es_pendiente)
    perfil.pendientes_activos = pendientes

    # Frecuencia y prioridad
    perfil.frecuencia = detectar_frecuencia(perfil.total_correos)
    perfil.nivel_prioridad = detectar_prioridad(
        perfil.total_correos, pendientes, perfil.tono_predominante
    )

    # Patrones de días
    patron_semana = calcular_patron_dias(correos)
    perfil.patron_dias_semana = json.dumps(patron_semana, ensure_ascii=False)

    patron_mes = calcular_patron_dias_mes(correos)
    perfil.patron_dias_mes = json.dumps(patron_mes, ensure_ascii=False)

    # Adjuntos
    tipos_adj, tasa_adj = calcular_adjuntos(correos)
    perfil.adjuntos_frecuentes = json.dumps(tipos_adj, ensure_ascii=False)
    perfil.tasa_adjuntos = tasa_adj

    # Última solicitud
    try:
        ultimos = sorted(
            [c for c in correos if c.resumen],
            key=lambda x: (
                x.fecha if x.fecha and hasattr(x.fecha, 'year')
                else datetime.datetime.min
            ),
            reverse=True,
        )
        if ultimos:
            perfil.ultima_solicitud = ultimos[0].resumen
    except Exception:
        pass

    # Resumen para humanos
    dia_frecuente = max(patron_semana, key=patron_semana.get) if patron_semana else ''
    temas_str = ', '.join(list(conteo_temas.keys())[:5]) if conteo_temas else 'variados'
    perfil.resumen_perfil = (
        f"{perfil.nombre or perfil.email} — {perfil.tipo} — "
        f"{perfil.total_correos} correos — "
        f"tono: {perfil.tono_predominante} — "
        f"frecuencia: {perfil.frecuencia} — "
        f"temas: {temas_str} — "
        f"pendientes: {pendientes} — "
        f"prioridad: {perfil.nivel_prioridad}"
        + (f" — escribe los {dia_frecuente}" if dia_frecuente else '')
        + (f" — adjunta docs ({int(tasa_adj*100)}%)" if tasa_adj > 0.3 else '')
    )

    # Contexto optimizado para IA
    perfil.contexto_ia = generar_contexto_ia(
        perfil, conteo_temas, patron_semana, tasa_adj, pendientes
    )

    perfil.clasificado = True
    perfil.save()