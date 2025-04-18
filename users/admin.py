from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerProfile, Address

class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = 'seller profile'

class UserAdmin(BaseUserAdmin):
    inlines = (SellerProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_seller', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_seller', 'phone_number')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('is_seller', 'phone_number')}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Address)