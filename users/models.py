from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model for IPO WebApp
    Extends Django's built-in User model with IPO-specific fields
    """
    
    # Personal Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True,
        help_text="Phone number for OTP verification"
    )
    
    date_of_birth = models.DateField(
        null=True, 
        blank=True,
        help_text="Date of birth for age verification"
    )
    
    # KYC Information
    pan_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        help_text="PAN number for tax compliance"
    )
    
    aadhar_number = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        help_text="Aadhar number for identity verification"
    )
    
    # Investor Category
    INVESTOR_CATEGORIES = [
        ('RETAIL', 'Retail Individual Investor (RII)'),
        ('HNI', 'High Net Worth Individual (HNI)'),
        ('QIB', 'Qualified Institutional Buyer (QIB)'),
        ('EMPLOYEE', 'Employee Category'),
    ]
    
    investor_category = models.CharField(
        max_length=10,
        choices=INVESTOR_CATEGORIES,
        default='RETAIL',
        help_text="Investor category for IPO application"
    )
    
    # Bank Details
    bank_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Primary bank for ASBA"
    )
    
    bank_account_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Bank account number for transactions"
    )
    
    ifsc_code = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        help_text="IFSC code of the bank branch"
    )
    
    # Demat Account
    demat_account_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Demat account for share allotment"
    )
    
    depository = models.CharField(
        max_length=10,
        choices=[('NSDL', 'NSDL'), ('CDSL', 'CDSL')],
        null=True,
        blank=True,
        help_text="Depository participant"
    )
    
    # Profile Information
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="Profile picture"
    )
    
    # Status Fields
    is_kyc_verified = models.BooleanField(
        default=False,
        help_text="KYC verification status"
    )
    
    is_phone_verified = models.BooleanField(
        default=False,
        help_text="Phone number verification status"
    )
    
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Email verification status"
    )
    
    # Address Information
    address_line_1 = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Address line 1"
    )
    
    address_line_2 = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Address line 2"
    )
    
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="City"
    )
    
    state = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="State"
    )
    
    pincode = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        help_text="Postal code"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    def get_full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_profile_complete(self):
        """Check if user profile is complete"""
        required_fields = [
            self.phone_number, self.date_of_birth, self.pan_number,
            self.bank_account_number, self.demat_account_number
        ]
        return all(field for field in required_fields)
    
    @property
    def can_apply_ipo(self):
        """Check if user can apply for IPO"""
        return (
            self.is_kyc_verified and 
            self.is_phone_verified and 
            self.is_profile_complete
        )