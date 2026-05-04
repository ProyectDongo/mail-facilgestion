import re
import json
import datetime

DOMINIO_INTERNO = 'micontable.cl'

DOMINIOS_PERSONALES = [
    'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
    'live.com', 'icloud.com', 'yahoo.es', 'hotmail.es',
]

DOMINIOS_PUBLICOS = [
    'sii.cl', 'dt.gob.cl', 'tgr.cl', 'previred.com',
    'achs.cl', 'ist.cl', 'mutual.cl', 'suseso.cl',
    'cmfchile.cl', 'bcn.cl', 'gob.cl', 'chile.cl',
    'caja-losandes.cl', 'consalud.cl', 'banmedica.cl',
]

TEMAS_KEYWORDS = {
    'f29': [
        'f29', 'iva', 'declaracion mensual', 'impuesto mensual',
        'debito fiscal', 'credito fiscal', 'modifcacion f29',
        'modificacion f29', 'declaracion iva',
    ],
    'f22': [
        'f22', 'declaracion anual', 'impuesto a la renta',
        'operacion renta', 'renta anual',
    ],
    'ppm': ['ppm', 'pago provisional', 'pagos provisionales mensuales'],

    'sii': [
        'sii', 'servicio de impuestos', 'timbre', 'folio',
        'contribuyente', 'boleta electronica', 'factura electronica',
        'sii.cl', 'cedible', 'acuse de recibo sii',
        'f.30', 'f30', 'creacion de obra','carpeta tributaria', 'solicitud de carpeta tributaria',
        'tramites rel', 'intranet', 'tramites sii', 'tramite sii', 'sii tramites',
    ],
    'tgr': [
        'tgr', 'tesoreria', 'tesorería', 'deuda fiscal',
        'convenio pago', 'tesoreria general',
    ],
    'inicio_termino_giro': [
        'inicio de actividades', 'termino de giro',
        'término de giro', 'giro comercial',
    ],
    'contrato_trabajo': [
        'contrato de trabajo', 'contrato laboral', 'anexo contrato',
        'anexo contraro', 'anexo de renovacion', 'renovacion contrato',
        'reajuste sueldo', 'reajuste de cargo', 'anexo reajuste',
        'horario de trabajo', 'revocacion de descuento',
        'jornada laboral', 'contratacion', 'parametros',
        'solicitud de parametros', 'modificacion de liquidacion',
        'solicitud de anexo', 'anexo horario', 'anexo firmado',
        'creacion de anexo','solicitud de contrato', 'solicitud de creacion de contrato',
        'contrato de sandra', 'contratacion y anexos', 'generar contrato',
        'solicitud de extension de contrato', 'informacion para contrato',
        'documento cambio de dia', 'anexos', 'contratos',
        'solicitud de rol', 'aumento de sueldo', 'cambio de cargo', 'cambio de jornada',
    ],
    'finiquito': [
        'finiquito', 'termino contrato', 'término contrato',
        'desvinculacion', 'desvinculación', 'termino de servicio',
        'término de servicio', 'término de obra', 'termino de obra',
        'solicitud de cartas de salida', 'cartas de salida',
    ],
    'renuncia': [
        'renuncia', 'renuncia voluntaria', 'carta de renuncia',
    ],
    'despido': [
        'despido', 'carta aviso', 'carta de despido',
        'necesidades empresa', 'articulo 161', 'articulo 159',
        'articulo 160', 'carta de aviso', 'cartas de aviso',
        'aviso por termino', 'solicitud de carta de aviso',
        'solicitud de cartas de aviso', 'personal 5 dias',
        'carta por falla', 'falla reiterada', 'carta de amonestacion',
        'amonestacion',
    ],
    'liquidacion_sueldo': [
        'liquidacion de sueldo', 'liquidación de sueldo',
        'sueldo bruto', 'sueldo liquido', 'remuneracion',
        'gratificacion', 'bono', 'informacion para liquidacion',
        'nomina', 'nómina', 'estado de pago', 'pagos mensuales',
        'ventas noviembre', 'ventas octubre', 'ventas mes',
        'proyeccion cierre','solicitud de liquidacion', 'liquidacion y anexo',
        'anticipos', 'anticipos mes', 'pago pensiones',
        'auxiliar cta clientes', 'planilla de costos',
        'compras enero', 'libros de compra ventas',
    ],
    'licencia_medica': [
        'licencia medica', 'licencia médica', 'reposo',
        'subsidio enfermedad', 'licencia',
        'aviso importante cotizaciones isapre', 'isapre consalud',
        'cotizaciones isapre',
    ],
    'vacaciones': [
        'vacaciones', 'feriado legal', 'dias habiles',
        'descanso anual', 'feriado progresivo', 'permiso vacaciones',
    ],
    'accidente_laboral': [
        'accidente laboral', 'accidente del trabajo', 'mutual',
        'achs', 'ist', 'mutual de seguridad', 'denuncia accidente',
        'inasistencia',
    ],
    'direccion_trabajo': [
        'direccion del trabajo', 'dirección del trabajo',
        'inspector del trabajo', 'mediacion laboral',
        'denuncia laboral', 'auditoria laboral', 'auditorias laborales',
        'envio de documentacion auditoria','notificacion reclamo', 'notificación de reclamo',
        'proceso de licitacion', 'causa romero',
        'carta notificacion decreto',
    ],
    'constitucion': [
        'constitucion de sociedad', 'constitución de sociedad',
        'sociedad limitada', 'spa', 'sociedad anonima',
        'escritura de constitucion',
    ],
    'modificacion': [
        'modificacion de estatutos', 'modificación de estatutos',
        'reforma estatutos', 'cambio de razon social',
    ],
    'poder_notarial': [
        'poder notarial', 'escritura publica', 'notaria',
        'notaría', 'protocolizacion',
    ],
    'balance': [
        'balance', 'estado financiero', 'estado de resultado',
        'utilidad', 'perdida', 'patrimonio',
        'balance noviembre', 'balance octubre', 'balance mes',
        'cierre año', 'proyeccion cierre año', 'cierre contable',
    ],
    'libro_contable': [
        'libro diario', 'libro mayor', 'libro de compras',
        'libro de ventas', 'contabilidad',
    ],
    'cuentas_cobrar': [
        'cuentas por cobrar', 'deudores', 'mora', 'cobranza',
        'factura pendiente',
    ],
    'cuentas_pagar': [
        'cuentas por pagar', 'proveedores', 'pago pendiente',
        'vencimiento pago', 'gasto comun', 'gasto común',
    ],
    'rendicion': [
        'rendicion', 'rendición', 'rendicion de gastos',
        'rendicion premios', 'rendicion fiesta', 'reembolso',
        'comprobante de gasto',
    ],
    'comprobante': [
        'comprobante', 'comprobantes', 'voucher',
        'notificacion pago beneficiario', 'pago beneficiario',
    ],
    'factura': [
        'factura', 'boleta', 'nota de venta',
        'documento tributario', 'dte', 'solicitud de boleta',
        'solicitud de guia', 'guia de despacho', 'detalle boletas',
        'boletas de garantia', 'anular guia',
        'orden de compra', 'cotizacion', 'factoring',
        'creacion de destinatario pyme', 'envio cotizacion',
    ],
    'nota_credito': [
        'nota de credito', 'nota de débito', 'nota de debito',
        'anulacion factura',
    ],
    'certificado': [
        'certificado', 'certificacion', 'constancia',
        'acreditacion', 'vbo', 'vºbº', 'firma cuota',
        'nomina colegiados', 'nómina colegiados',
        'pago bienestar', 'cuota regional', 'pago rifa',
        'doctos navidad', 'gastos aniversario',
        'autorización de firmas', 'autorizacion de firmas',
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
        'solicitud de documentacion', 'solicitud de documentos',
        'envio de documentacion', 'termino de servicios de contabilidad',
    ],
    'tarea_urgente': [
        'urgente', 'a la brevedad', 'lo antes posible',
        'vence hoy', 'vence mañana', 'plazo vencido',
        'necesito que envie', 'favor enviar',
    ],
    'consulta': [
        'consulta', 'quisiera saber', 'me podria informar',
        'podria indicarme', 'como se hace', 'cual es el procedimiento',
        'informacion kmch', 'informacion para',
    ],
    'coordinacion': [
        'reunion', 'reunión', 'llamada', 'videollamada',
        'nos juntamos', 'disponibilidad', 'capacitacion',
        'invitacion a capacitacion','invitacion a capacitacion', 'superir',
        'compra de camioneta',
    ],
    'confirmacion': [
        'confirmado', 'recibido', 'queda confirmado',
        'tome nota', 'enterado', 'ok listo',
    ],
    'seguimiento': [
        'seguimiento', 'recordatorio', 'quedamos pendientes',
        'hay novedades', 'en que estado', 'solicitud de informacion',
    ],
    'solicitud_fondos': [
        'solicitud de fondos', 'transferencia', 'transferencias',
        'cartola', 'cartola bci', 'estado de cuenta',
        'abono', 'cargo en cuenta',
        'pago rifa', 'pago bienestar',
        'anticipos', 'rifa',
    ],
    'notificacion_sii': [
        'notificacion sii', 'no-reply@sii.cl',
        'acuse de recibo sii',
    ],
    'notificacion_banco': [
        'banco', 'transferencia recibida', 'abono en cuenta',
        'cargo en cuenta', 'estado de cuenta',
        'mora presunta', 'aviso para regularizacion',
        'cotizaciones previsionales',
    ],
    'notificacion_prevision': [
        'afp', 'cotizacion previsional', 'previred',
        'fonasa', 'isapre cotizacion', 'cotizaciones de salud',
        'pago cotizaciones', 'trabajadores no vigentes',
        'nueva masvida','deuda por cotizaciones', 'cotizaciones de seguridad social',
        'nueva cotizacion de cargo', 'webinar',
        'prestamo blando',
    ],
    'spam': [
        'unsubscribe', 'darse de baja', 'oferta exclusiva',
        'gana dinero', 'click aqui', 'promocion especial',
        'message delivery failure', 'mail delivery system',
        'corona de caridad', 'tu opinion vale oro',
        'lista regalos rifa', 'foto de','mensaje de prueba', 'microsoft outlook',
        'comunidad de edificio', 'cosmocentro',
        'smart tv', 'tiko tiki', 'parrilla',
        'desayuno exclusivo', 'rrhh defontana',
        'link nuevo', 'link',
    ],
}

TONO_KEYWORDS = {
    'urgente': [
        'urgente', 'urgencia', 'inmediato', 'a la brevedad',
        'plazo vencido', 'vence hoy', 'critico', 'crítico',
    ],
    'formal': [
        'estimado', 'distinguido', 'cordialmente', 'atentamente',
        'saludos cordiales', 'me dirijo', 'mediante la presente',
        'de mi consideracion',
    ],
    'informal': [
        'hola', 'hey', 'buen dia', 'buenas', 'gracias',
        'saludos', 'cómo estás', 'como estas', 'te escribo',
    ],
    'tecnico': [
        'servidor', 'api', 'sistema', 'base de datos',
        'configuracion', 'version', 'proceso', 'modulo',
    ],
}

PENDIENTE_KEYWORDS = [
    'urgente', 'a la brevedad', 'lo antes posible',
    'plazo vencido', 'vence hoy', 'vence mañana',
    'necesito que envie', 'necesito que me envie',
    'favor enviar', 'por favor enviar', 'pendiente de envio',
    'estamos esperando', 'sin respuesta', 'no hemos recibido',
    'mora presunta', 'aviso para regularizacion',
]

PREFIJOS_RE = re.compile(
    r'^(re|rv|rr|fw|fwd|reenviado|respuesta|resp)[\s:\-]+',
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
        3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo'
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


def calcular_adjuntos(correos) -> dict:
    tipos = {}
    total = len(correos)
    con_adjuntos = 0
    for c in correos:
        if c.tiene_adjuntos:
            con_adjuntos += 1
            for nombre in c.nombres_adjuntos.split(','):
                nombre = nombre.strip().lower()
                if '.' in nombre:
                    ext = nombre.rsplit('.', 1)[-1]
                    tipos[ext] = tipos.get(ext, 0) + 1
    tasa = round(con_adjuntos / total, 2) if total > 0 else 0.0
    return tipos, tasa


def actualizar_perfil(perfil, correos):
    if not correos:
        return

    tonos = [c.tono for c in correos if c.tono != 'desconocido']
    if tonos:
        perfil.tono_predominante = max(set(tonos), key=tonos.count)

    temas = [c.tema for c in correos if c.tema != 'otro']
    conteo_temas = {}
    for t in temas:
        conteo_temas[t] = conteo_temas.get(t, 0) + 1
    perfil.temas_frecuentes = json.dumps(conteo_temas, ensure_ascii=False)

    pendientes = sum(1 for c in correos if c.es_pendiente)
    perfil.pendientes_activos = pendientes
    perfil.frecuencia = detectar_frecuencia(perfil.total_correos)
    perfil.nivel_prioridad = detectar_prioridad(
        perfil.total_correos, pendientes, perfil.tono_predominante
    )

    patron_semana = calcular_patron_dias(correos)
    perfil.patron_dias_semana = json.dumps(patron_semana, ensure_ascii=False)

    patron_mes = calcular_patron_dias_mes(correos)
    perfil.patron_dias_mes = json.dumps(patron_mes, ensure_ascii=False)

    tipos_adj, tasa_adj = calcular_adjuntos(correos)
    perfil.adjuntos_frecuentes = json.dumps(tipos_adj, ensure_ascii=False)
    perfil.tasa_adjuntos = tasa_adj

    try:
        ultimos = sorted(
            [c for c in correos if c.resumen],
            key=lambda x: x.fecha if x.fecha and hasattr(x.fecha, 'year') else datetime.datetime.min,
            reverse=True
        )
        if ultimos:
            perfil.ultima_solicitud = ultimos[0].resumen
    except Exception:
        pass

    dia_frecuente = ''
    if patron_semana:
        dia_frecuente = max(patron_semana, key=patron_semana.get)

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
        + (f" — adjunta documentos ({int(tasa_adj*100)}%)" if tasa_adj > 0.3 else '')
    )

    perfil.clasificado = True
    perfil.save()