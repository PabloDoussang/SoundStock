from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['rol'] = 'Administrador'
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    ROLES = [('Administrador', 'Administrador'), ('Operador', 'Operador'), ('Consulta', 'Consulta')]
    username = models.CharField('nombre de usuario', max_length=150, unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='Consulta')
    objects = UsuarioManager()

    def save(self, *args, **kwargs):
        self.is_staff = self.is_superuser = self.rol == 'Administrador'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.username
