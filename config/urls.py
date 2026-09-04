from django.urls import path, include
from warehouse import views
urlpatterns = [
    path('ingresar/', views.login, name='login'),
    path('salir/', views.logout, name='logout'),
    path('', include('warehouse.urls')),
]
