from rest_framework import serializers
from .models import IPO


class IPOListSerializer(serializers.ModelSerializer):
    """
    Serializer for IPO list view (lightweight)
    """
    price_range = serializers.ReadOnlyField()
    min_investment = serializers.ReadOnlyField()
    is_open = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_closed = serializers.ReadOnlyField()
    days_to_open = serializers.ReadOnlyField()
    days_to_close = serializers.ReadOnlyField()
    
    class Meta:
        model = IPO
        fields = [
            'id', 'company_name', 'company_logo', 'status',
            'price_range', 'lot_size', 'min_investment',
            'issue_open_date', 'issue_close_date', 'listing_date',
            'issue_size', 'total_subscription', 'listing_exchange',
            'is_open', 'is_upcoming', 'is_closed',
            'days_to_open', 'days_to_close', 'created_at'
        ]


class IPODetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed IPO view
    """
    price_range = serializers.ReadOnlyField()
    min_investment = serializers.ReadOnlyField()
    is_open = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_closed = serializers.ReadOnlyField()
    days_to_open = serializers.ReadOnlyField()
    days_to_close = serializers.ReadOnlyField()
    
    # Subscription statistics
    subscription_stats = serializers.SerializerMethodField()
    allocation_details = serializers.SerializerMethodField()
    
    class Meta:
        model = IPO
        fields = [
            'id', 'company_name', 'company_logo', 'description',
            'status', 'price_band_min', 'price_band_max', 'price_range',
            'lot_size', 'min_investment', 'face_value', 'market_cap',
            'issue_size', 'issue_open_date', 'issue_close_date',
            'listing_date', 'listing_exchange', 'prospectus_url',
            'drhp_url', 'objectives', 'registrar_name', 'lead_managers',
            'is_open', 'is_upcoming', 'is_closed',
            'days_to_open', 'days_to_close',
            'subscription_stats', 'allocation_details',
            'created_at', 'updated_at'
        ]
    
    def get_subscription_stats(self, obj):
        """Get subscription statistics"""
        return {
            'total_subscription': float(obj.total_subscription),
            'retail_subscription': float(obj.retail_subscription),
            'hni_subscription': float(obj.hni_subscription),
            'qib_subscription': float(obj.qib_subscription),
        }
    
    def get_allocation_details(self, obj):
        """Get allocation percentages"""
        return {
            'retail_allocation': float(obj.retail_allocation),
            'hni_allocation': float(obj.hni_allocation),
            'qib_allocation': float(obj.qib_allocation),
        }


class IPOCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating IPO (admin only)
    """
    class Meta:
        model = IPO
        fields = [
            'company_name', 'company_logo', 'description', 'status',
            'issue_size', 'price_band_min', 'price_band_max',
            'lot_size', 'face_value', 'market_cap',
            'issue_open_date', 'issue_close_date', 'listing_date',
            'retail_allocation', 'hni_allocation', 'qib_allocation',
            'listing_exchange', 'prospectus_url', 'drhp_url',
            'objectives', 'registrar_name', 'lead_managers'
        ]
    
    def validate(self, attrs):
        """Validate IPO data"""
        # Check if price band is valid
        if attrs.get('price_band_min') and attrs.get('price_band_max'):
            if attrs['price_band_min'] >= attrs['price_band_max']:
                raise serializers.ValidationError(
                    "Minimum price must be less than maximum price"
                )
        
        # Check if dates are valid
        if attrs.get('issue_open_date') and attrs.get('issue_close_date'):
            if attrs['issue_open_date'] >= attrs['issue_close_date']:
                raise serializers.ValidationError(
                    "Issue open date must be before close date"
                )
        
        # Check if allocations add up to 100%
        retail = attrs.get('retail_allocation', 0)
        hni = attrs.get('hni_allocation', 0)
        qib = attrs.get('qib_allocation', 0)
        
        total_allocation = retail + hni + qib
        if abs(total_allocation - 100) > 0.01:  # Allow small floating point differences
            raise serializers.ValidationError(
                "Total allocation must equal 100%"
            )
        
        return attrs


class IPOFilterSerializer(serializers.Serializer):
    """
    Serializer for IPO filtering and search
    """
    status = serializers.ChoiceField(
        choices=IPO.IPO_STATUS_CHOICES,
        required=False
    )
    exchange = serializers.ChoiceField(
        choices=IPO.EXCHANGE_CHOICES,
        required=False
    )
    price_min = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    price_max = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    search = serializers.CharField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'issue_open_date', '-issue_open_date',
            'issue_close_date', '-issue_close_date',
            'company_name', '-company_name',
            'issue_size', '-issue_size'
        ],
        required=False,
        default='-issue_open_date'
    )