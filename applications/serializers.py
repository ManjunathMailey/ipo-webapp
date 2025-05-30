from rest_framework import serializers
from .models import IPOApplication, BidDetail, ApplicationDocument
from ipos.serializers import IPOListSerializer


class IPOApplicationListSerializer(serializers.ModelSerializer):
    """
    Serializer for IPO application list view
    """
    ipo = IPOListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    number_of_lots = serializers.ReadOnlyField()
    can_be_modified = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = IPOApplication
        fields = [
            'id', 'application_number', 'user_name', 'ipo',
            'quantity', 'bid_price', 'total_amount', 'number_of_lots',
            'status', 'payment_status', 'allotted_quantity',
            'allotment_price', 'refund_amount', 'applied_at',
            'can_be_modified', 'can_be_cancelled'
        ]


class IPOApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed IPO application view
    """
    ipo = IPOListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    number_of_lots = serializers.ReadOnlyField()
    can_be_modified = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    profit_loss = serializers.ReadOnlyField()
    
    class Meta:
        model = IPOApplication
        fields = [
            'id', 'application_number', 'user_name', 'ipo',
            'quantity', 'bid_price', 'total_amount', 'number_of_lots',
            'status', 'payment_status', 'bank_name', 'bank_account_number',
            'pan_number', 'demat_account', 'allotted_quantity',
            'allotment_price', 'refund_amount', 'applied_at',
            'updated_at', 'confirmed_at', 'allotment_date',
            'can_be_modified', 'can_be_cancelled', 'profit_loss'
        ]


class IPOApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating IPO application
    """
    class Meta:
        model = IPOApplication
        fields = [
            'ipo', 'quantity', 'bid_price', 'bank_name',
            'bank_account_number', 'pan_number', 'demat_account'
        ]
    
    def validate_quantity(self, value):
        """Validate quantity is multiple of lot size"""
        ipo = self.initial_data.get('ipo')
        if ipo:
            from ipos.models import IPO
            try:
                ipo_obj = IPO.objects.get(id=ipo)
                if value % ipo_obj.lot_size != 0:
                    raise serializers.ValidationError(
                        f"Quantity must be multiple of lot size ({ipo_obj.lot_size})"
                    )
            except IPO.DoesNotExist:
                raise serializers.ValidationError("Invalid IPO")
        return value
    
    def validate_bid_price(self, value):
        """Validate bid price is within price band"""
        ipo = self.initial_data.get('ipo')
        if ipo:
            from ipos.models import IPO
            try:
                ipo_obj = IPO.objects.get(id=ipo)
                if not (ipo_obj.price_band_min <= value <= ipo_obj.price_band_max):
                    raise serializers.ValidationError(
                        f"Bid price must be between ₹{ipo_obj.price_band_min} and ₹{ipo_obj.price_band_max}"
                    )
            except IPO.DoesNotExist:
                raise serializers.ValidationError("Invalid IPO")
        return value
    
    def validate(self, attrs):
        """Validate IPO application"""
        ipo = attrs.get('ipo')
        user = self.context['request'].user
        
        # Check if IPO is open for subscription
        if not ipo.is_open:
            raise serializers.ValidationError("IPO is not open for subscription")
        
        # Check if user can apply for IPO
        if not user.can_apply_ipo:
            raise serializers.ValidationError(
                "Complete your profile and KYC verification to apply for IPO"
            )
        
        # Check if user already applied for this IPO
        if IPOApplication.objects.filter(user=user, ipo=ipo).exists():
            raise serializers.ValidationError(
                "You have already applied for this IPO"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create IPO application"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class IPOApplicationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating IPO application
    """
    class Meta:
        model = IPOApplication
        fields = ['quantity', 'bid_price']
    
    def validate(self, attrs):
        """Validate application can be modified"""
        if not self.instance.can_be_modified:
            raise serializers.ValidationError(
                "Application cannot be modified at this time"
            )
        return attrs


class BidDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for bid details
    """
    bid_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = BidDetail
        fields = ['id', 'bid_price', 'quantity', 'bid_amount', 'created_at']


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for application documents
    """
    class Meta:
        model = ApplicationDocument
        fields = [
            'id', 'document_type', 'document_file',
            'description', 'uploaded_at'
        ]


class IPOApplicationStatsSerializer(serializers.Serializer):
    """
    Serializer for IPO application statistics
    """
    total_applications = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    retail_applications = serializers.IntegerField()
    hni_applications = serializers.IntegerField()
    qib_applications = serializers.IntegerField()
    subscription_ratio = serializers.DecimalField(max_digits=8, decimal_places=2)