from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('movimientos/', views.movimientos, name='movimientos'),
    path('movimientos/nuevo/', views.nuevo_movimiento, name='movimiento_crear'),
    path('reportes/', views.reportes, name='reportes'),
    path('ubicaciones/', views.ubicaciones, name='ubicaciones'),
    path('exportar/<str:tipo>/', views.exportar, name='exportar'),
]
