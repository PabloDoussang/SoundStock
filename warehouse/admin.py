from django.contrib import admin
from .models import Product, Movement
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, AdminUserCreationForm
from django.contrib.auth.models import User
from .usernames import SpacedUsernameMixin

class WarehouseUserChangeForm(SpacedUsernameMixin, UserChangeForm):
    username = forms.CharField(max_length=150, label='Nombre de usuario')

class WarehouseUserCreationForm(SpacedUsernameMixin, AdminUserCreationForm):
    username = forms.CharField(max_length=150, label='Nombre de usuario')

admin.site.unregister(User)
@admin.register(User)
class WarehouseUserAdmin(UserAdmin):
    form = WarehouseUserChangeForm
    add_form = WarehouseUserCreationForm
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code','name','category','location','stock','minimum','active']
    search_fields = ['code','name','location']
    list_filter = ['category','active']
    readonly_fields = ['code','name','category','location','stock','minimum','active','updated_at']
    def has_add_permission(self,request): return False
    def has_delete_permission(self,request,obj=None): return False
@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['id','product','kind','delta','before','after','user','created_at']
    list_filter = ['kind']
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
admin.site.site_header = 'Music Pro · Administración'
