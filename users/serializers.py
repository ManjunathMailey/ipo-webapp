from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'investor_category'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate login credentials"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include username and password")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    full_name = serializers.SerializerMethodField()
    is_profile_complete = serializers.ReadOnlyField()
    can_apply_ipo = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'investor_category',
            'pan_number', 'aadhar_number', 'bank_name', 'bank_account_number',
            'ifsc_code', 'demat_account_number', 'depository',
            'address_line_1', 'address_line_2', 'city', 'state', 'pincode',
            'is_kyc_verified', 'is_phone_verified', 'is_email_verified',
            'is_profile_complete', 'can_apply_ipo', 'date_joined'
        ]
        read_only_fields = [
            'id', 'username', 'is_kyc_verified', 'is_phone_verified',
            'is_email_verified', 'date_joined'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'pan_number', 'aadhar_number', 'bank_name', 'bank_account_number',
            'ifsc_code', 'demat_account_number', 'depository',
            'address_line_1', 'address_line_2', 'city', 'state', 'pincode'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value