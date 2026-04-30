from django.urls import path
from . import views

urlpatterns = [
    # Sistema
    path('estado/',                views.estado,       name='correos_estado'),

    # Búsqueda general
    path('buscar/',                views.buscar,        name='correos_buscar'),

    # Perfiles
    path('perfiles/',              views.perfiles,      name='correos_perfiles'),
    path('perfil/<str:email>/',    views.perfil,        name='correos_perfil'),

    # Urgentes
    path('urgentes/',              views.urgentes,      name='correos_urgentes'),

    # Documentos legales
    path('documentos/',            views.documentos,    name='correos_documentos'),

    # Endpoint principal para IAs
    path('ia/',                    views.contexto_ia,   name='correos_ia'),
]