from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista, name='productos'),
    path('nuevo/', views.crear, name='producto_crear'),
    path('<int:pk>/editar/', views.editar, name='producto_editar'),
    path('<int:pk>/archivar/', views.archivar, name='producto_archivar'),
    path('<int:pk>/eliminar/', views.eliminar, name='producto_eliminar'),
]
