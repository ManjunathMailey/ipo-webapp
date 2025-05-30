from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import IPO
from .serializers import (
    IPOListSerializer, IPODetailSerializer,
    IPOCreateUpdateSerializer, IPOFilterSerializer
)


class IPOListView(generics.ListAPIView):
    """
    API view to list all IPOs with filtering and search
    """
    queryset = IPO.objects.all()
    serializer_class = IPOListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'listing_exchange']
    search_fields = ['company_name', 'description']
    ordering_fields = ['issue_open_date', 'issue_close_date', 'company_name', 'issue_size']
    ordering = ['-issue_open_date']
    
    def get_queryset(self):
        queryset = IPO.objects.all()
        
        # Custom filtering
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        exchange_filter = self.request.query_params.get('exchange')
        if exchange_filter:
            queryset = queryset.filter(listing_exchange=exchange_filter)
        
        price_min = self.request.query_params.get('price_min')
        if price_min:
            queryset = queryset.filter(price_band_min__gte=price_min)
        
        price_max = self.request.query_params.get('price_max')
        if price_max:
            queryset = queryset.filter(price_band_max__lte=price_max)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset


class IPODetailView(generics.RetrieveAPIView):
    """
    API view to get detailed IPO information
    """
    queryset = IPO.objects.all()
    serializer_class = IPODetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'


class IPOCreateView(generics.CreateAPIView):
    """
    API view to create new IPO (admin only)
    """
    queryset = IPO.objects.all()
    serializer_class = IPOCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]


class IPOUpdateView(generics.UpdateAPIView):
    """
    API view to update IPO (admin only)
    """
    queryset = IPO.objects.all()
    serializer_class = IPOCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'id'


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ipo_categories_view(request):
    """
    API view to get IPOs categorized by status
    """
    from django.utils import timezone
    today = timezone.now().date()
    
    # Update IPO statuses
    for ipo in IPO.objects.all():
        ipo.update_status()
    
    upcoming = IPO.objects.filter(status='UPCOMING').order_by('issue_open_date')
    open_ipos = IPO.objects.filter(status='OPEN').order_by('issue_close_date')
    closed = IPO.objects.filter(status='CLOSED').order_by('-issue_close_date')
    listed = IPO.objects.filter(status='LISTED').order_by('-listing_date')
    
    return Response({
        'upcoming': IPOListSerializer(upcoming[:10], many=True).data,
        'open': IPOListSerializer(open_ipos[:10], many=True).data,
        'closed': IPOListSerializer(closed[:10], many=True).data,
        'listed': IPOListSerializer(listed[:10], many=True).data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ipo_statistics_view(request):
    """
    API view to get IPO market statistics
    """
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    
    today = timezone.now().date()
    current_year = today.year
    
    # Basic statistics
    total_ipos = IPO.objects.count()
    active_ipos = IPO.objects.filter(status='OPEN').count()
    upcoming_ipos = IPO.objects.filter(status='UPCOMING').count()
    listed_ipos = IPO.objects.filter(status='LISTED').count()
    
    # This year's statistics
    this_year_ipos = IPO.objects.filter(
        issue_open_date__year=current_year
    )
    
    # Market statistics
    total_issue_size = IPO.objects.aggregate(
        total=Sum('issue_size')
    )['total'] or 0
    
    avg_subscription = IPO.objects.aggregate(
        avg=Avg('total_subscription')
    )['avg'] or 0
    
    # Top performing IPOs (by subscription)
    top_subscribed = IPO.objects.filter(
        total_subscription__gt=0
    ).order_by('-total_subscription')[:5]
    
    return Response({
        'overview': {
            'total_ipos': total_ipos,
            'active_ipos': active_ipos,
            'upcoming_ipos': upcoming_ipos,
            'listed_ipos': listed_ipos,
            'total_issue_size': float(total_issue_size),
            'avg_subscription': float(avg_subscription),
        },
        'this_year': {
            'total_ipos': this_year_ipos.count(),
            'total_issue_size': float(
                this_year_ipos.aggregate(
                    total=Sum('issue_size')
                )['total'] or 0
            ),
        },
        'top_subscribed': IPOListSerializer(top_subscribed, many=True).data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ipo_search_view(request):
    """
    API view for advanced IPO search
    """
    search_query = request.query_params.get('q', '')
    
    if not search_query:
        return Response({
            'results': [],
            'message': 'Please provide a search query'
        }, status=status.HTTP_200_OK)
    
    # Search in multiple fields
    ipos = IPO.objects.filter(
        Q(company_name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(objectives__icontains=search_query) |
        Q(registrar_name__icontains=search_query)
    ).distinct()
    
    serializer = IPOListSerializer(ipos, many=True)
    
    return Response({
        'results': serializer.data,
        'count': ipos.count(),
        'query': search_query
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def update_ipo_status_view(request, ipo_id):
    """
    API view to manually update IPO status
    """
    try:
        ipo = IPO.objects.get(id=ipo_id)
        new_status = request.data.get('status')
        
        if new_status not in dict(IPO.IPO_STATUS_CHOICES):
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ipo.status = new_status
        ipo.save()
        
        return Response({
            'message': 'IPO status updated successfully',
            'ipo': IPODetailSerializer(ipo).data
        }, status=status.HTTP_200_OK)
        
    except IPO.DoesNotExist:
        return Response({
            'error': 'IPO not found'
        }, status=status.HTTP_404_NOT_FOUND)