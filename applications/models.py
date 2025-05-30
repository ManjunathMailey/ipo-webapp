from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class IPOApplication(models.Model):
    """
    IPO Application Model - Represents a user's application for an IPO
    """
    
    # Primary Keys and References
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique application ID"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ipo_applications',
        help_text="User who applied for the IPO"
    )
    
    ipo = models.ForeignKey(
        'ipos.IPO',
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="IPO for which application is made"
    )
    
    # Application Details
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares applied for"
    )
    
    bid_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per share bid by the applicant"
    )
    
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total application amount"
    )
    
    # Application Status
    APPLICATION_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('ALLOTTED', 'Allotted'),
        ('NOT_ALLOTTED', 'Not Allotted'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    status = models.CharField(
        max_length=15,
        choices=APPLICATION_STATUS_CHOICES,
        default='DRAFT',
        help_text="Current status of the application"
    )
    
    # Payment Information
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Payment Pending'),
        ('BLOCKED', 'Amount Blocked'),
        ('CONFIRMED', 'Payment Confirmed'),
        ('REFUNDED', 'Amount Refunded'),
        ('FAILED', 'Payment Failed'),
    ]
    
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        help_text="Payment status"
    )
    
    # ASBA Details
    bank_name = models.CharField(
        max_length=100,
        help_text="Bank for ASBA mandate"
    )
    
    bank_account_number = models.CharField(
        max_length=20,
        help_text="Bank account number for ASBA"
    )
    
    # Allotment Details
    allotted_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Number of shares allotted"
    )
    
    allotment_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final allotment price per share"
    )
    
    refund_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount to be refunded"
    )
    
    # Additional Information
    application_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Application number from registrar"
    )
    
    pan_number = models.CharField(
        max_length=10,
        help_text="PAN number used for application"
    )
    
    demat_account = models.CharField(
        max_length=20,
        help_text="Demat account for share credit"
    )
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    allotment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ipo_applications'
        verbose_name = 'IPO Application'
        verbose_name_plural = 'IPO Applications'
        unique_together = ['user', 'ipo']  # One application per user per IPO
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.ipo.company_name} - {self.quantity} shares"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total amount"""
        self.total_amount = self.quantity * self.bid_price
        
        # Generate application number if not exists
        if not self.application_number and self.status == 'SUBMITTED':
            self.application_number = self.generate_application_number()
        
        super().save(*args, **kwargs)
    
    def generate_application_number(self):
        """Generate unique application number"""
        import random
        import string
        
        # Format: IPO + Company Code + Random 6 digits
        company_code = ''.join(self.ipo.company_name.split())[:3].upper()
        random_digits = ''.join(random.choices(string.digits, k=6))
        return f"IPO{company_code}{random_digits}"
    
    @property
    def is_multiple_of_lot_size(self):
        """Check if applied quantity is multiple of lot size"""
        return self.quantity % self.ipo.lot_size == 0
    
    @property
    def number_of_lots(self):
        """Calculate number of lots applied"""
        return self.quantity // self.ipo.lot_size
    
    @property
    def can_be_modified(self):
        """Check if application can be modified"""
        return self.status in ['DRAFT', 'SUBMITTED'] and self.ipo.is_open
    
    @property
    def can_be_cancelled(self):
        """Check if application can be cancelled"""
        return self.status in ['DRAFT', 'SUBMITTED', 'CONFIRMED'] and self.ipo.is_open
    
    @property
    def profit_loss(self):
        """Calculate profit/loss if listed"""
        if self.ipo.status == 'LISTED' and self.allotted_quantity > 0:
            # This would need current market price - placeholder for now
            return Decimal('0.00')
        return None


class BidDetail(models.Model):
    """
    Bid Detail Model - For multiple price bids in book building process
    """
    
    application = models.ForeignKey(
        IPOApplication,
        on_delete=models.CASCADE,
        related_name='bid_details',
        help_text="Related IPO application"
    )
    
    bid_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Bid price for this lot"
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares for this bid price"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bid_details'
        verbose_name = 'Bid Detail'
        verbose_name_plural = 'Bid Details'
        ordering = ['-bid_price']
    
    def __str__(self):
        return f"{self.quantity} shares @ ₹{self.bid_price}"
    
    @property
    def bid_amount(self):
        """Calculate amount for this bid"""
        return self.quantity * self.bid_price


class ApplicationDocument(models.Model):
    """
    Application Document Model - For storing application related documents
    """
    
    application = models.ForeignKey(
        IPOApplication,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Related IPO application"
    )
    
    DOCUMENT_TYPE_CHOICES = [
        ('APPLICATION_FORM', 'Application Form'),
        ('ASBA_FORM', 'ASBA Form'),
        ('PAN_CARD', 'PAN Card'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('DEMAT_STATEMENT', 'Demat Statement'),
        ('OTHER', 'Other'),
    ]
    
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Type of document"
    )
    
    document_file = models.FileField(
        upload_to='application_documents/',
        help_text="Uploaded document file"
    )
    
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Document description"
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_documents'
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.application}"