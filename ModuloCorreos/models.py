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

    email                = models.EmailField(unique=True)
    nombre               = models.CharField(max_length=200, blank=True)
    dominio              = models.CharField(max_length=200, blank=True)
    empresa              = models.CharField(max_length=200, blank=True)
    rut                  = models.CharField(max_length=20, blank=True)
    tipo                 = models.CharField(max_length=20, choices=TIPO_CHOICES, default='desconocido')
    total_correos        = models.IntegerField(default=0)
    primer_contacto      = models.DateTimeField(auto_now_add=True)
    ultimo_contacto      = models.DateTimeField(auto_now=True)
    tono_predominante    = models.CharField(max_length=20, choices=TONO_CHOICES, default='desconocido')
    frecuencia           = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='esporadica')
    nivel_prioridad      = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    temas_frecuentes     = models.TextField(blank=True)
    resumen_perfil       = models.TextField(blank=True)
    ultima_solicitud     = models.TextField(blank=True)
    pendientes_activos   = models.IntegerField(default=0)
    es_empresa           = models.BooleanField(default=False)
    clasificado          = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} <{self.email}>"

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
        # Documental
        ('factura',              'Factura / Boleta'),
        ('nota_credito',         'Nota de crédito / débito'),
        ('certificado',          'Certificado'),
        ('declaracion_jurada',   'Declaración jurada'),
        # Operacional
        ('tarea_urgente',        'Tarea urgente'),
        ('consulta',             'Consulta / Duda'),
        ('coordinacion',         'Coordinación / Reunión'),
        ('confirmacion',         'Confirmación / OK'),
        ('seguimiento',          'Seguimiento / Recordatorio'),
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
    contenido    = models.TextField(blank=True)  # texto extraído del PDF
    tags         = models.TextField(blank=True)  # palabras clave separadas por coma
    subido_en    = models.DateTimeField(auto_now_add=True)
    activo       = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo
