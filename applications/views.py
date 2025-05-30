from rest_framework import status, generics, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from .models import IPOApplication, BidDetail, ApplicationDocument
from .serializers import (
    IPOApplicationListSerializer, IPOApplicationDetailSerializer,
    IPOApplicationCreateSerializer, IPOApplicationUpdateSerializer,
    BidDetailSerializer, ApplicationDocumentSerializer,
    IPOApplicationStatsSerializer
)


class IPOApplicationListCreateView(generics.ListCreateAPIView):
    """
    API view to list and create IPO applications
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IPOApplicationCreateSerializer
        return IPOApplicationListSerializer
    
    def get_queryset(self):
        """Get applications for the current user"""
        return IPOApplication.objects.filter(
            user=self.request.user
        ).select_related('ipo').order_by('-applied_at')
    
    def create(self, request, *args, **kwargs):
        """Create new IPO application"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            
            return Response({
                'message': 'IPO application submitted successfully',
                'application': IPOApplicationDetailSerializer(application).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IPOApplicationDetailView(generics.RetrieveAPIView):
    """
    API view to get detailed IPO application
    """
    serializer_class = IPOApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get applications for the current user only"""
        return IPOApplication.objects.filter(
            user=self.request.user
        ).select_related('ipo')


class IPOApplicationUpdateView(generics.UpdateAPIView):
    """
    API view to update IPO application
    """
    serializer_class = IPOApplicationUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get applications for the current user only"""
        return IPOApplication.objects.filter(
            user=self.request.user
        ).select_related('ipo')
    
    def update(self, request, *args, **kwargs):
        """Update IPO application"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if not instance.can_be_modified:
            return Response({
                'error': 'Application cannot be modified at this time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Application updated successfully',
                'application': IPOApplicationDetailSerializer(instance).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_application_view(request, id):
    """
    API view to cancel IPO application
    """
    try:
        application = IPOApplication.objects.get(
            id=id, user=request.user
        )
        
        if not application.can_be_cancelled:
            return Response({
                'error': 'Application cannot be cancelled at this time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        application.status = 'CANCELLED'
        application.save()
        
        return Response({
            'message': 'Application cancelled successfully',
            'application': IPOApplicationDetailSerializer(application).data
        }, status=status.HTTP_200_OK)
        
    except IPOApplication.DoesNotExist:
        return Response({
            'error': 'Application not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def application_stats_view(request):
    """
    API view to get user's application statistics
    """
    user = request.user
    applications = IPOApplication.objects.filter(user=user)
    
    stats = {
        'total_applications': applications.count(),
        'submitted_applications': applications.filter(status='SUBMITTED').count(),
        'confirmed_applications': applications.filter(status='CONFIRMED').count(),
        'allotted_applications': applications.filter(status='ALLOTTED').count(),
        'rejected_applications': applications.filter(status='REJECTED').count(),
        'total_invested': applications.filter(
            status__in=['SUBMITTED', 'CONFIRMED', 'ALLOTTED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_refund': applications.aggregate(
            total=Sum('refund_amount')
        )['total'] or 0,
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ipo_application_stats_view(request, ipo_id):
    """
    API view to get IPO-specific application statistics
    """
    from ipos.models import IPO
    
    try:
        ipo = IPO.objects.get(id=ipo_id)
    except IPO.DoesNotExist:
        return Response({
            'error': 'IPO not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    applications = IPOApplication.objects.filter(ipo=ipo)
    
    # Basic statistics
    total_applications = applications.count()
    total_amount = applications.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Category-wise statistics
    retail_apps = applications.filter(user__investor_category='RETAIL').count()
    hni_apps = applications.filter(user__investor_category='HNI').count()
    qib_apps = applications.filter(user__investor_category='QIB').count()
    
    # Calculate subscription ratio (simplified)
    if ipo.issue_size > 0:
        subscription_ratio = (total_amount / (ipo.issue_size * 10000000)) * 100  # Convert crores to actual amount
    else:
        subscription_ratio = 0
    
    stats = {
        'total_applications': total_applications,
        'total_amount': total_amount,
        'retail_applications': retail_apps,
        'hni_applications': hni_apps,
        'qib_applications': qib_apps,
        'subscription_ratio': round(subscription_ratio, 2),
    }
    
    return Response(stats, status=status.HTTP_200_OK)


class ApplicationDocumentListCreateView(generics.ListCreateAPIView):
    """
    API view to list and upload application documents
    """
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        return ApplicationDocument.objects.filter(
            application__id=application_id,
            application__user=self.request.user
        )
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        try:
            application = IPOApplication.objects.get(
                id=application_id,
                user=self.request.user
            )
            serializer.save(application=application)
        except IPOApplication.DoesNotExist:
            raise serializers.ValidationError("Application not found")


class ApplicationDocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    API view to retrieve and delete application documents
    """
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'document_id'
    
    def get_queryset(self):
        return ApplicationDocument.objects.filter(
            application__user=self.request.user
        )