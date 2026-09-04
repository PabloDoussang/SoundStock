from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth
urlpatterns = [
    path('admin/', admin.site.urls),
    path('ingresar/', auth.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('salir/', auth.LogoutView.as_view(), name='logout'),
    path('', include('warehouse.urls')),
]
