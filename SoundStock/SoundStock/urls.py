from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

admin.site.site_header = 'SoundStock · Administración'
admin.site.site_title = 'SoundStock Admin'
admin.site.index_title = 'Usuarios, catálogo e inventario'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ingresar/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('productos/', include('catalogo.urls')),
    path('', include('inventario.urls')),
]
