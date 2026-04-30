from django.contrib import admin
from .models import CuentaIMAP, SyncEstado, PerfilRemitente, CorreoCopia, DocumentoLegal ,CorreoEnviado, ParConversacion

@admin.register(CuentaIMAP)
class CuentaIMAPAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'host', 'usuario', 'activa']

@admin.register(SyncEstado)
class SyncEstadoAdmin(admin.ModelAdmin):
    list_display = ['ultimo_uid', 'actualizado']

@admin.register(PerfilRemitente)
class PerfilRemitenteAdmin(admin.ModelAdmin):
    list_display  = ['email', 'nombre', 'tipo', 'total_correos', 'nivel_prioridad', 'frecuencia', 'pendientes_activos']
    search_fields = ['email', 'nombre', 'empresa', 'rut']
    list_filter   = ['tipo', 'nivel_prioridad', 'frecuencia', 'tono_predominante']

@admin.register(CorreoCopia)
class CorreoCopiaAdmin(admin.ModelAdmin):
    list_display  = ['asunto', 'de', 'tema', 'tono', 'es_pendiente', 'fecha']
    search_fields = ['asunto', 'de', 'cuerpo']
    list_filter   = ['tema', 'tono', 'es_pendiente', 'clasificado']

@admin.register(DocumentoLegal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    list_display  = ['titulo', 'tipo', 'activo', 'subido_en']
    search_fields = ['titulo', 'descripcion', 'tags', 'contenido']
    list_filter   = ['tipo', 'activo']


@admin.register(CorreoEnviado)
class CorreoEnviadoAdmin(admin.ModelAdmin):
    list_display  = ['asunto', 'para', 'fecha', 'tema']
    search_fields = ['asunto', 'para', 'cuerpo']
    list_filter   = ['tema']

@admin.register(ParConversacion)
class ParConversacionAdmin(admin.ModelAdmin):
    list_display  = ['tema', 'remitente_email', 'es_respuesta', 'creado_en']
    search_fields = ['remitente_email', 'tema']
    list_filter   = ['tema', 'es_respuesta']
