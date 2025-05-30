from django.contrib import admin
from django.utils.html import format_html
from .models import IPO


@admin.register(IPO)
class IPOAdmin(admin.ModelAdmin):
    """
    IPO Admin interface
    """
    
    # Fields to display in the list view
    list_display = [
        'company_name', 'status', 'price_range_display', 
        'issue_open_date', 'issue_close_date', 'issue_size',
        'total_subscription', 'created_at'
    ]
    
    # Fields to filter by
    list_filter = [
        'status', 'listing_exchange', 'issue_open_date', 
        'issue_close_date', 'created_at'
    ]
    
    # Fields to search by
    search_fields = [
        'company_name', 'description', 'registrar_name'
    ]
    
    # Default ordering
    ordering = ['-issue_open_date']
    
    # Fields that are read-only
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    # Organize fields in sections
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'company_name', 'company_logo', 'description',
                'status'
            )
        }),
        ('Financial Details', {
            'fields': (
                'issue_size', 'price_band_min', 'price_band_max',
                'lot_size', 'face_value', 'market_cap'
            )
        }),
        ('Important Dates', {
            'fields': (
                'issue_open_date', 'issue_close_date', 'listing_date'
            )
        }),
        ('Allocation Details', {
            'fields': (
                'retail_allocation', 'hni_allocation', 'qib_allocation'
            )
        }),
        ('Subscription Statistics', {
            'fields': (
                'total_subscription', 'retail_subscription',
                'hni_subscription', 'qib_subscription'
            )
        }),
        ('Exchange & Documents', {
            'fields': (
                'listing_exchange', 'prospectus_url', 'drhp_url'
            )
        }),
        ('Additional Information', {
            'fields': (
                'objectives', 'registrar_name', 'lead_managers'
            )
        }),
        ('System Information', {
            'fields': (
                'created_at', 'updated_at'
            )
        }),
    )
    
    # Custom display methods
    def price_range_display(self, obj):
        """Display formatted price range"""
        return f"₹{obj.price_band_min} - ₹{obj.price_band_max}"
    price_range_display.short_description = "Price Range"
    
    def min_investment_display(self, obj):
        """Display minimum investment amount"""
        return f"₹{obj.min_investment:,.2f}"
    min_investment_display.short_description = "Minimum Investment"
    
    def days_remaining_display(self, obj):
        """Display days remaining based on status"""
        if obj.is_upcoming:
            days = obj.days_to_open
            return format_html(
                '<span style="color: orange;">Opens in {} days</span>',
                days
            )
        elif obj.is_open:
            days = obj.days_to_close
            return format_html(
                '<span style="color: green;">Closes in {} days</span>',
                days
            )
        else:
            return format_html(
                '<span style="color: red;">Closed</span>'
            )
    days_remaining_display.short_description = "Status"
    
    # Admin actions
    actions = ['update_status', 'mark_as_open', 'mark_as_closed']
    
    def update_status(self, request, queryset):
        """Update IPO status based on dates"""
        updated_count = 0
        for ipo in queryset:
            old_status = ipo.status
            ipo.update_status()
            if ipo.status != old_status:
                updated_count += 1
        
        self.message_user(
            request, 
            f'{updated_count} IPO statuses updated successfully.'
        )
    update_status.short_description = "Update status based on dates"
    
    def mark_as_open(self, request, queryset):
        """Mark selected IPOs as open"""
        updated = queryset.update(status='OPEN')
        self.message_user(
            request, 
            f'{updated} IPOs marked as open successfully.'
        )
    mark_as_open.short_description = "Mark selected IPOs as open"
    
    def mark_as_closed(self, request, queryset):
        """Mark selected IPOs as closed"""
        updated = queryset.update(status='CLOSED')
        self.message_user(
            request, 
            f'{updated} IPOs marked as closed successfully.'
        )
    mark_as_closed.short_description = "Mark selected IPOs as closed"
    
    # Custom save method
    def save_model(self, request, obj, form, change):
        """Auto-update status when saving"""
        super().save_model(request, obj, form, change)
        obj.update_status()