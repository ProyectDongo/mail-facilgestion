from django.urls import path
from . import views

urlpatterns = [
    path('buscar/', views.buscar,  name='correos_buscar'),
    path('estado/', views.estado,  name='correos_estado'),
]