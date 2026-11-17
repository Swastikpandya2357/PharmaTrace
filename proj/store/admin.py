from django.contrib import admin
from .models import register, adregister, OTP, AdminOTP, SCNProduct, SCNOrder, SCNLatencyLog


class RegiAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email')

admin.site.register(register, RegiAdmin)


class AdRegisterAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    search_fields = ('username', 'email')

admin.site.register(adregister, AdRegisterAdmin)


class SCNProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'stock_quantity', 'lead_time_hours', 'distributor')
    list_filter = ('category', 'distributor')
    search_fields = ('sku', 'name')

admin.site.register(SCNProduct, SCNProductAdmin)


class SCNOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'product', 'quantity', 'retailer_name', 'status', 'latency_recorded_hours', 'ordered_at')
    list_filter = ('status', 'ordered_at')
    search_fields = ('order_id', 'retailer_name', 'retailer_email')

admin.site.register(SCNOrder, SCNOrderAdmin)


class SCNLatencyLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'event', 'recorded_by', 'role', 'timestamp', 'latency_benchmark')
    list_filter = ('role', 'timestamp')

admin.site.register(SCNLatencyLog, SCNLatencyLogAdmin)


admin.site.register(OTP)
admin.site.register(AdminOTP)
