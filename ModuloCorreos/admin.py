from django.contrib import admin
from .models import SyncEstado, PerfilRemitente, CorreoCopia


@admin.register(SyncEstado)
class SyncEstadoAdmin(admin.ModelAdmin):
    list_display = ['ultimo_uid', 'actualizado']


@admin.register(PerfilRemitente)
class PerfilRemitenteAdmin(admin.ModelAdmin):
    list_display  = ['email', 'nombre', 'dominio', 'total_correos', 'ultimo_contacto']
    search_fields = ['email', 'nombre', 'dominio']


@admin.register(CorreoCopia)
class CorreoCopiaAdmin(admin.ModelAdmin):
    list_display  = ['asunto', 'de', 'fecha', 'tiene_adjuntos']
    search_fields = ['asunto', 'de', 'cuerpo', 'remitente__email']
    list_filter   = ['tiene_adjuntos', 'fecha']