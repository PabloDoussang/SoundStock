from django.urls import path
from . import views
urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path('inventario/',views.products,name='products'),
    path('inventario/nuevo/',views.product_edit,name='product_new'),
    path('inventario/<int:pk>/editar/',views.product_edit,name='product_edit'),
    path('inventario/<int:pk>/archivar/',views.product_archive,name='product_archive'),
    path('stock/',views.movement_new,name='movement_new'),
    path('movimientos/',views.movements,name='movements'),
    path('reportes/',views.reports,name='reports'),
    path('ubicaciones/',views.locations,name='locations'),
    path('exportar/<str:kind>/',views.export,name='export'),
    path('usuarios/',views.users,name='users'),
    path('usuarios/nuevo/',views.user_edit,name='user_new'),
    path('usuarios/<int:pk>/editar/',views.user_edit,name='user_edit'),
]
