from django.contrib import admin
from .models import *

class ProfileAdmin(admin.ModelAdmin):
    # แก้ไข list_display โดยใช้ข้อมูลจาก `User` (Profile.user)
    list_display = ('user', 'get_first_name', 'get_last_name', 'gender', 'age', 'location')

    # เมธอดสำหรับดึง `first_name` และ `last_name` จาก `User`
    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.admin_order_field = 'user__first_name'  # ให้สามารถสั่งเรียงลำดับได้ใน Admin
    get_first_name.short_description = 'First Name'  # ชื่อคอลัมน์ใน Admin

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.admin_order_field = 'user__last_name'
    get_last_name.short_description = 'Last Name'

# DoctorProfileAdmin สำหรับแสดงข้อมูลใน Admin ของ DoctorProfile
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'work_location', 'session_rate', 'service_mode', 'contact')


@admin.register(DoctorApprovalRequest)
class DoctorApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'work_location', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'work_location']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('ข้อมูลผู้ใช้', {
            'fields': ('user', 'title')
        }),
        ('ข้อมูลการทำงาน', {
            'fields': ('work_location',)
        }),
        ('ข้อมูลติดต่อ', {
            'fields': ('address', 'district', 'province', 'postal_code', 'phone')
        }),
        ('เอกสารและหมายเหตุ', {
            'fields': ('document', 'note')
        }),
        ('สถานะและเวลา', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    def has_add_permission(self, request):
        return False


admin.site.register(Profile, ProfileAdmin)
admin.site.register(DoctorProfile, DoctorProfileAdmin)
admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Result)