from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin with IPO-specific fields
    """
    
    # Fields to display in the user list
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'phone_number', 'investor_category', 'is_kyc_verified',
        'is_phone_verified', 'date_joined'
    ]
    
    # Fields to filter by
    list_filter = [
        'investor_category', 'is_kyc_verified', 'is_phone_verified',
        'is_email_verified', 'depository', 'is_staff', 'is_active',
        'date_joined'
    ]
    
    # Fields to search by
    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'phone_number', 'pan_number'
    ]
    
    # Organize fields in sections
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Personal Information', {
            'fields': (
                'phone_number', 'date_of_birth', 'profile_picture'
            )
        }),
        ('KYC Information', {
            'fields': (
                'pan_number', 'aadhar_number', 'investor_category'
            )
        }),
        ('Bank Details', {
            'fields': (
                'bank_name', 'bank_account_number', 'ifsc_code'
            )
        }),
        ('Demat Account', {
            'fields': (
                'demat_account_number', 'depository'
            )
        }),
        ('Address Information', {
            'fields': (
                'address_line_1', 'address_line_2', 'city', 
                'state', 'pincode'
            )
        }),
        ('Verification Status', {
            'fields': (
                'is_kyc_verified', 'is_phone_verified', 'is_email_verified'
            )
        }),
    )
    
    # Fields for adding new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'investor_category'
            )
        }),
    )
    
    # Enable actions
    actions = ['verify_kyc', 'verify_phone', 'verify_email']
    
    def verify_kyc(self, request, queryset):
        """Admin action to verify KYC"""
        updated = queryset.update(is_kyc_verified=True)
        self.message_user(request, f'{updated} users KYC verified successfully.')
    verify_kyc.short_description = "Mark selected users as KYC verified"
    
    def verify_phone(self, request, queryset):
        """Admin action to verify phone"""
        updated = queryset.update(is_phone_verified=True)
        self.message_user(request, f'{updated} users phone verified successfully.')
    verify_phone.short_description = "Mark selected users as phone verified"
    
    def verify_email(self, request, queryset):
        """Admin action to verify email"""
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users email verified successfully.')
    verify_email.short_description = "Mark selected users as email verified"