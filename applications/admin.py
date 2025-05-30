from django.contrib import admin
from django.utils.html import format_html
from .models import IPOApplication, BidDetail, ApplicationDocument


class BidDetailInline(admin.TabularInline):
    """
    Inline admin for bid details
    """
    model = BidDetail
    extra = 1
    fields = ['bid_price', 'quantity', 'bid_amount']
    readonly_fields = ['bid_amount']


class ApplicationDocumentInline(admin.TabularInline):
    """
    Inline admin for application documents
    """
    model = ApplicationDocument
    extra = 0
    fields = ['document_type', 'document_file', 'description']


@admin.register(IPOApplication)
class IPOApplicationAdmin(admin.ModelAdmin):
    """
    IPO Application Admin interface
    """
    
    # Inline models
    inlines = [BidDetailInline, ApplicationDocumentInline]
    
    # Fields to display in the list view
    list_display = [
        'application_number', 'user', 'ipo', 'quantity', 
        'bid_price', 'total_amount', 'status', 'payment_status',
        'applied_at'
    ]
    
    # Fields to filter by
    list_filter = [
        'status', 'payment_status', 'ipo__status', 
        'user__investor_category', 'applied_at'
    ]
    
    # Fields to search by
    search_fields = [
        'application_number', 'user__username', 'user__email',
        'ipo__company_name', 'pan_number'
    ]
    
    # Default ordering
    ordering = ['-applied_at']
    
    # Fields that are read-only
    readonly_fields = [
        'id', 'total_amount', 'applied_at', 'updated_at',
        'number_of_lots_display', 'profit_loss_display'
    ]
    
    # Organize fields in sections
    fieldsets = (
        ('Application Details', {
            'fields': (
                'id', 'user', 'ipo', 'application_number', 'status'
            )
        }),
        ('Bid Information', {
            'fields': (
                'quantity', 'bid_price', 'total_amount', 'number_of_lots_display'
            )
        }),
        ('Payment & Bank Details', {
            'fields': (
                'payment_status', 'bank_name', 'bank_account_number'
            )
        }),
        ('Identity Information', {
            'fields': (
                'pan_number', 'demat_account'
            )
        }),
        ('Allotment Details', {
            'fields': (
                'allotted_quantity', 'allotment_price', 'refund_amount',
                'allotment_date', 'profit_loss_display'
            )
        }),
        ('Timestamps', {
            'fields': (
                'applied_at', 'updated_at', 'confirmed_at'
            )
        }),
    )
    
    # Custom display methods
    def number_of_lots_display(self, obj):
        """Display number of lots"""
        return f"{obj.number_of_lots} lots"
    number_of_lots_display.short_description = "Number of Lots"
    
    def profit_loss_display(self, obj):
        """Display profit/loss if applicable"""
        profit_loss = obj.profit_loss
        if profit_loss is not None:
            if profit_loss > 0:
                return format_html(
                    '<span style="color: green;">+₹{:,.2f}</span>',
                    profit_loss
                )
            elif profit_loss < 0:
                return format_html(
                    '<span style="color: red;">-₹{:,.2f}</span>',
                    abs(profit_loss)
                )
            else:
                return "₹0.00"
        return "N/A"
    profit_loss_display.short_description = "Profit/Loss"
    
    # Admin actions
    actions = [
        'confirm_applications', 'reject_applications', 
        'mark_payment_confirmed', 'process_allotment'
    ]
    
    def confirm_applications(self, request, queryset):
        """Confirm selected applications"""
        updated = queryset.filter(status='SUBMITTED').update(status='CONFIRMED')
        self.message_user(
            request, 
            f'{updated} applications confirmed successfully.'
        )
    confirm_applications.short_description = "Confirm selected applications"
    
    def reject_applications(self, request, queryset):
        """Reject selected applications"""
        updated = queryset.filter(
            status__in=['SUBMITTED', 'CONFIRMED']
        ).update(status='REJECTED')
        self.message_user(
            request, 
            f'{updated} applications rejected successfully.'
        )
    reject_applications.short_description = "Reject selected applications"
    
    def mark_payment_confirmed(self, request, queryset):
        """Mark payment as confirmed"""
        updated = queryset.update(payment_status='CONFIRMED')
        self.message_user(
            request, 
            f'{updated} payments marked as confirmed.'
        )
    mark_payment_confirmed.short_description = "Mark payment as confirmed"
    
    def process_allotment(self, request, queryset):
        """Process allotment for applications"""
        # This is a simplified allotment process
        for application in queryset.filter(status='CONFIRMED'):
            # Simple logic: allot 50% of applied quantity
            application.allotted_quantity = application.quantity // 2
            application.allotment_price = application.ipo.price_band_max
            application.status = 'ALLOTTED' if application.allotted_quantity > 0 else 'NOT_ALLOTTED'
            application.save()
        
        self.message_user(
            request, 
            f'Allotment processed for {queryset.count()} applications.'
        )
    process_allotment.short_description = "Process allotment (Demo)"


@admin.register(BidDetail)
class BidDetailAdmin(admin.ModelAdmin):
    """
    Bid Detail Admin interface
    """
    
    list_display = [
        'application', 'bid_price', 'quantity', 'bid_amount', 'created_at'
    ]
    
    list_filter = ['bid_price', 'created_at']
    
    search_fields = [
        'application__user__username', 'application__ipo__company_name'
    ]
    
    readonly_fields = ['bid_amount', 'created_at']


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    """
    Application Document Admin interface
    """
    
    list_display = [
        'application', 'document_type', 'description', 'uploaded_at'
    ]
    
    list_filter = ['document_type', 'uploaded_at']
    
    search_fields = [
        'application__user__username', 'application__ipo__company_name',
        'description'
    ]
    
    readonly_fields = ['uploaded_at']