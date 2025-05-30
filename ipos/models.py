from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class IPO(models.Model):
    """
    IPO Model - Represents an Initial Public Offering
    """
    
    # Basic Company Information
    company_name = models.CharField(
        max_length=200,
        help_text="Name of the company going public"
    )
    
    company_logo = models.ImageField(
        upload_to='company_logos/',
        null=True,
        blank=True,
        help_text="Company logo image"
    )
    
    # IPO Details
    issue_size = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total issue size in crores"
    )
    
    price_band_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum price per share"
    )
    
    price_band_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum price per share"
    )
    
    lot_size = models.PositiveIntegerField(
        help_text="Minimum number of shares per application"
    )
    
    # Important Dates
    issue_open_date = models.DateField(
        help_text="Date when IPO opens for subscription"
    )
    
    issue_close_date = models.DateField(
        help_text="Date when IPO closes for subscription"
    )
    
    listing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected listing date on stock exchange"
    )
    
    # IPO Status
    IPO_STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('OPEN', 'Open for Subscription'),
        ('CLOSED', 'Closed'),
        ('ALLOTMENT', 'Allotment Process'),
        ('LISTED', 'Listed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    status = models.CharField(
        max_length=15,
        choices=IPO_STATUS_CHOICES,
        default='UPCOMING',
        help_text="Current status of the IPO"
    )
    
    # Allocation Details
    retail_allocation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('35.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage allocated for retail investors"
    )
    
    hni_allocation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage allocated for HNI investors"
    )
    
    qib_allocation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('50.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage allocated for QIB investors"
    )
    
    # Company Financial Information
    face_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text="Face value per share"
    )
    
    market_cap = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected market capitalization in crores"
    )
    
    # Exchange Information
    EXCHANGE_CHOICES = [
        ('BSE', 'Bombay Stock Exchange'),
        ('NSE', 'National Stock Exchange'),
        ('BOTH', 'Both BSE and NSE'),
    ]
    
    listing_exchange = models.CharField(
        max_length=10,
        choices=EXCHANGE_CHOICES,
        default='BOTH',
        help_text="Stock exchange for listing"
    )
    
    # Documents
    prospectus_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to IPO prospectus document"
    )
    
    drhp_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to Draft Red Herring Prospectus"
    )
    
    # Additional Information
    description = models.TextField(
        help_text="Brief description about the company and IPO"
    )
    
    objectives = models.TextField(
        null=True,
        blank=True,
        help_text="Objects of the issue"
    )
    
    # Subscription Statistics
    total_subscription = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total subscription times (e.g., 2.5x)"
    )
    
    retail_subscription = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retail category subscription times"
    )
    
    hni_subscription = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="HNI category subscription times"
    )
    
    qib_subscription = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="QIB category subscription times"
    )
    
    # Registrar Information
    registrar_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Name of the registrar"
    )
    
    # Lead Managers
    lead_managers = models.TextField(
        null=True,
        blank=True,
        help_text="Lead managers for the IPO (comma separated)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ipos'
        verbose_name = 'IPO'
        verbose_name_plural = 'IPOs'
        ordering = ['-issue_open_date']
    
    def __str__(self):
        return f"{self.company_name} IPO"
    
    @property
    def is_open(self):
        """Check if IPO is currently open for subscription"""
        today = timezone.now().date()
        return (
            self.status == 'OPEN' and
            self.issue_open_date <= today <= self.issue_close_date
        )
    
    @property
    def is_upcoming(self):
        """Check if IPO is upcoming"""
        today = timezone.now().date()
        return self.issue_open_date > today
    
    @property
    def is_closed(self):
        """Check if IPO subscription is closed"""
        today = timezone.now().date()
        return self.issue_close_date < today or self.status == 'CLOSED'
    
    @property
    def days_to_open(self):
        """Calculate days remaining to open"""
        if self.is_upcoming:
            return (self.issue_open_date - timezone.now().date()).days
        return 0
    
    @property
    def days_to_close(self):
        """Calculate days remaining to close"""
        if self.is_open:
            return (self.issue_close_date - timezone.now().date()).days
        return 0
    
    @property
    def price_range(self):
        """Get formatted price range"""
        return f"₹{self.price_band_min} - ₹{self.price_band_max}"
    
    @property
    def min_investment(self):
        """Calculate minimum investment amount"""
        return self.lot_size * self.price_band_max
    
    def update_status(self):
        """Auto-update IPO status based on dates"""
        today = timezone.now().date()
        
        if today < self.issue_open_date:
            self.status = 'UPCOMING'
        elif self.issue_open_date <= today <= self.issue_close_date:
            self.status = 'OPEN'
        elif today > self.issue_close_date:
            if self.listing_date and today >= self.listing_date:
                self.status = 'LISTED'
            else:
                self.status = 'CLOSED'
        
        self.save()
    
    def get_allocation_by_category(self, category):
        """Get allocation percentage by investor category"""
        allocation_map = {
            'RETAIL': self.retail_allocation,
            'HNI': self.hni_allocation,
            'QIB': self.qib_allocation,
        }
        return allocation_map.get(category, Decimal('0.00'))