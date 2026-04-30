from django.db import models

class SyncEstado(models.Model):
    """Guarda el último UID procesado para reanudar sin repetir."""
    ultimo_uid  = models.IntegerField(default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado de sincronización'

class PerfilRemitente(models.Model):
    email           = models.EmailField(unique=True)
    nombre          = models.CharField(max_length=200, blank=True)
    dominio         = models.CharField(max_length=200, blank=True)
    total_correos   = models.IntegerField(default=0)
    primer_contacto = models.DateTimeField(auto_now_add=True)
    ultimo_contacto = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} <{self.email}>"

class CorreoCopia(models.Model):
    remitente        = models.ForeignKey(PerfilRemitente, on_delete=models.SET_NULL,
                                         null=True, related_name='correos')
    message_id       = models.CharField(max_length=500, unique=True)
    de               = models.CharField(max_length=500)
    para             = models.TextField(blank=True)
    asunto           = models.CharField(max_length=1000, blank=True)
    fecha            = models.DateTimeField(null=True, blank=True)
    cuerpo           = models.TextField(blank=True)
    tiene_adjuntos   = models.BooleanField(default=False)
    nombres_adjuntos = models.TextField(blank=True)
    uid_imap         = models.IntegerField(db_index=True)
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.asunto} — {self.de}"