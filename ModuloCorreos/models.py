from django.db import models


class CuentaIMAP(models.Model):
    nombre  = models.CharField(max_length=100)
    host    = models.CharField(max_length=200)
    puerto  = models.IntegerField(default=993)
    usuario = models.CharField(max_length=200)
    activa  = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class SyncEstado(models.Model):
    ultimo_uid  = models.IntegerField(default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado de sincronización'


class PerfilRemitente(models.Model):
    TIPO_CHOICES = [
        ('cliente',           'Cliente'),
        ('proveedor',         'Proveedor'),
        ('organismo_publico', 'Organismo Público'),
        ('interno',           'Interno'),
        ('desconocido',       'Desconocido'),
    ]
    FRECUENCIA_CHOICES = [
        ('diaria',     'Diaria'),
        ('semanal',    'Semanal'),
        ('mensual',    'Mensual'),
        ('esporadica', 'Esporádica'),
    ]
    PRIORIDAD_CHOICES = [
        ('alta',  'Alta'),
        ('media', 'Media'),
        ('baja',  'Baja'),
    ]
    TONO_CHOICES = [
        ('formal',       'Formal'),
        ('informal',     'Informal'),
        ('tecnico',      'Técnico'),
        ('comercial',    'Comercial'),
        ('desconocido',  'Desconocido'),
    ]

    # ── Identidad ─────────────────────────────────────────────────────
    email                = models.EmailField(unique=True)
    nombre               = models.CharField(max_length=200, blank=True)
    dominio              = models.CharField(max_length=200, blank=True)
    empresa              = models.CharField(max_length=200, blank=True)
    rut                  = models.CharField(max_length=20, blank=True)
    tipo                 = models.CharField(max_length=20, choices=TIPO_CHOICES, default='desconocido')
    es_empresa           = models.BooleanField(default=False)

    # ── Actividad general ─────────────────────────────────────────────
    total_correos        = models.IntegerField(default=0)
    primer_contacto      = models.DateTimeField(auto_now_add=True)
    ultimo_contacto      = models.DateTimeField(auto_now=True)
    frecuencia           = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='esporadica')
    nivel_prioridad      = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    pendientes_activos   = models.IntegerField(default=0)

    # ── Comportamiento comunicacional ─────────────────────────────────
    tono_predominante    = models.CharField(max_length=20, choices=TONO_CHOICES, default='desconocido')

    # ── Temas y patrones (JSON) ───────────────────────────────────────
    temas_frecuentes     = models.TextField(blank=True)
    # Ej: {"finiquito": 12, "contrato_trabajo": 8, "liquidacion_sueldo": 5}

    patron_dias_semana   = models.TextField(blank=True)
    # Ej: {"lunes": 8, "martes": 3, "miercoles": 5, ...}
    # → "Katherine siempre escribe los lunes"

    patron_dias_mes      = models.TextField(blank=True)
    # Ej: {"25": 12, "1": 8, "30": 6}
    # → "Diana manda remuneraciones el día 25"

    adjuntos_frecuentes  = models.TextField(blank=True)
    # Ej: {"pdf": 45, "xlsx": 12, "docx": 3}
    # → "Siempre adjunta PDFs"

    tipos_adjuntos_tema  = models.TextField(blank=True)
    # Ej: {"finiquito": ["pdf"], "liquidacion_sueldo": ["xlsx", "pdf"]}
    # → "Para finiquitos siempre manda PDF"

    palabras_clave_propias = models.TextField(blank=True)
    # Ej: ["kaufmann", "lidia", "cossio", "auxiliar de aseo"]
    # → Términos únicos de ese cliente para identificar sus correos

    tiempo_respuesta_promedio = models.FloatField(default=0.0)
    # Horas promedio entre su solicitud y nuestra respuesta

    tasa_adjuntos        = models.FloatField(default=0.0)
    # % de sus correos que traen adjuntos (0.0 - 1.0)

    # ── Resúmenes para IA ─────────────────────────────────────────────
    resumen_perfil       = models.TextField(blank=True)
    # Texto libre generado automáticamente para contexto de IA
    # Ej: "Katherine de Kaufmann — cliente frecuente — solicita contratos
    #      y finiquitos — escribe los lunes — tono formal — alta prioridad"

    ultima_solicitud     = models.TextField(blank=True)
    # Último resumen de lo que pidió

    respuesta_tipica     = models.TextField(blank=True)
    # Cómo responde normalmente la oficina a este cliente (aprendido de pares)
    # Ej: "Se adjunta documento PDF con firma. Plazo habitual: 24h."

    contexto_ia          = models.TextField(blank=True)
    # JSON completo listo para pasar como contexto a la IA
    # Incluye: temas, patrones, ejemplos de respuesta, tono esperado

    clasificado          = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} <{self.email}>"

    def to_contexto_ia(self):
        """
        Genera un diccionario rico para pasar como contexto a la IA
        cuando llega un correo nuevo de este remitente.
        """
        import json
        temas = {}
        try:
            temas = json.loads(self.temas_frecuentes) if self.temas_frecuentes else {}
        except Exception:
            pass

        patron_dias = {}
        try:
            patron_dias = json.loads(self.patron_dias_semana) if self.patron_dias_semana else {}
        except Exception:
            pass

        return {
            'cliente': self.nombre or self.email,
            'empresa': self.empresa,
            'email': self.email,
            'tipo': self.tipo,
            'tono_habitual': self.tono_predominante,
            'frecuencia_contacto': self.frecuencia,
            'prioridad': self.nivel_prioridad,
            'total_correos_historico': self.total_correos,
            'temas_que_solicita': temas,
            'dia_semana_frecuente': max(patron_dias, key=patron_dias.get) if patron_dias else '',
            'adjunta_documentos': self.tasa_adjuntos > 0.3,
            'tiempo_respuesta_esperado_horas': round(self.tiempo_respuesta_promedio, 1),
            'ultima_solicitud': self.ultima_solicitud,
            'respuesta_tipica_oficina': self.respuesta_tipica,
            'palabras_clave': self.palabras_clave_propias,
        }


class CorreoCopia(models.Model):
    TEMA_CHOICES = [
        # Tributario
        ('f29',                  'F29 / IVA mensual'),
        ('f22',                  'F22 / Renta anual'),
        ('ppm',                  'PPM'),
        ('sii',                  'SII / Timbre / RUT'),
        ('tgr',                  'TGR / Tesorería'),
        ('inicio_termino_giro',  'Inicio / Término de giro'),
        # Laboral
        ('contrato_trabajo',     'Contrato de trabajo'),
        ('finiquito',            'Finiquito'),
        ('renuncia',             'Renuncia voluntaria'),
        ('despido',              'Despido / Desvinculación'),
        ('liquidacion_sueldo',   'Liquidación de sueldo'),
        ('licencia_medica',      'Licencia médica'),
        ('vacaciones',           'Vacaciones / Feriado'),
        ('accidente_laboral',    'Accidente laboral / Mutual'),
        ('direccion_trabajo',    'Dirección del Trabajo'),
        # Societario
        ('constitucion',         'Constitución de empresa'),
        ('modificacion',         'Modificación de estatutos'),
        ('poder_notarial',       'Poder notarial / Escritura'),
        # Contabilidad
        ('balance',              'Balance / Estado financiero'),
        ('libro_contable',       'Libro diario / Mayor'),
        ('cuentas_cobrar',       'Cuentas por cobrar'),
        ('cuentas_pagar',        'Cuentas por pagar'),
        ('rendicion',            'Rendición de gastos'),
        ('comprobante',          'Comprobante de pago'),
        # Documental
        ('factura',              'Factura / Boleta'),
        ('nota_credito',         'Nota de crédito / débito'),
        ('certificado',          'Certificado'),
        ('declaracion_jurada',   'Declaración jurada'),
        ('documento_trabajador', 'Documento de trabajador'),
        # Operacional
        ('tarea_urgente',        'Tarea urgente'),
        ('consulta',             'Consulta / Duda'),
        ('coordinacion',         'Coordinación / Reunión'),
        ('confirmacion',         'Confirmación / OK'),
        ('seguimiento',          'Seguimiento / Recordatorio'),
        ('solicitud_fondos',     'Solicitud de fondos'),
        # Automático
        ('notificacion_sii',     'Notificación SII'),
        ('notificacion_banco',   'Notificación banco'),
        ('notificacion_prevision','Notificación previsión'),
        ('spam',                 'Spam / Publicidad'),
        ('otro',                 'Otro'),
    ]

    TONO_CHOICES = [
        ('formal',      'Formal'),
        ('informal',    'Informal'),
        ('tecnico',     'Técnico'),
        ('urgente',     'Urgente'),
        ('desconocido', 'Desconocido'),
    ]

    remitente         = models.ForeignKey(PerfilRemitente, on_delete=models.SET_NULL, null=True, related_name='correos')
    message_id        = models.CharField(max_length=500, unique=True)
    de                = models.CharField(max_length=500)
    para              = models.TextField(blank=True)
    asunto            = models.CharField(max_length=1000, blank=True)
    fecha             = models.DateTimeField(null=True, blank=True)
    cuerpo            = models.TextField(blank=True)
    tiene_adjuntos    = models.BooleanField(default=False)
    nombres_adjuntos  = models.TextField(blank=True)
    uid_imap          = models.IntegerField(db_index=True)
    creado_en         = models.DateTimeField(auto_now_add=True)
    tema              = models.CharField(max_length=30, choices=TEMA_CHOICES, default='otro')
    tono              = models.CharField(max_length=20, choices=TONO_CHOICES, default='desconocido')
    resumen           = models.TextField(blank=True)
    es_pendiente      = models.BooleanField(default=False)
    clasificado       = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.asunto} — {self.de}"


class DocumentoLegal(models.Model):
    TIPO_CHOICES = [
        ('ley',          'Ley'),
        ('reglamento',   'Reglamento'),
        ('circular',     'Circular SII'),
        ('dictamen',     'Dictamen DT'),
        ('paper',        'Paper / Documento interno'),
        ('otro',         'Otro'),
    ]

    titulo       = models.CharField(max_length=300)
    tipo         = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ley')
    descripcion  = models.TextField(blank=True)
    archivo      = models.FileField(upload_to='documentos_legales/', null=True, blank=True)
    url          = models.URLField(blank=True)
    contenido    = models.TextField(blank=True)
    tags         = models.TextField(blank=True)
    subido_en    = models.DateTimeField(auto_now_add=True)
    activo       = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo


class CorreoEnviado(models.Model):
    message_id       = models.CharField(max_length=500, unique=True)
    in_reply_to      = models.CharField(max_length=500, blank=True)
    para             = models.TextField(blank=True)
    asunto           = models.CharField(max_length=1000, blank=True)
    fecha            = models.DateTimeField(null=True, blank=True)
    cuerpo           = models.TextField(blank=True)
    tiene_adjuntos   = models.BooleanField(default=False)
    nombres_adjuntos = models.TextField(blank=True)
    uid_imap         = models.IntegerField(db_index=True)
    tema             = models.CharField(max_length=30, blank=True)
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"→ {self.para[:50]} | {self.asunto[:50]}"


class ParConversacion(models.Model):
    """
    Par solicitud → respuesta.
    Base del entrenamiento de la IA para aprender cómo responde la oficina.
    """
    correo_recibido = models.ForeignKey(
        CorreoCopia, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pares_como_solicitud'
    )
    correo_enviado  = models.ForeignKey(
        CorreoEnviado, on_delete=models.CASCADE,
        related_name='pares_como_respuesta'
    )
    remitente_email = models.CharField(max_length=200, blank=True)
    tema            = models.CharField(max_length=30, blank=True)
    es_respuesta    = models.BooleanField(default=False)
    creado_en       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f"Par [{self.tema}] → {self.remitente_email}"