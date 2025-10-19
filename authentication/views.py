from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, views, permissions, viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer, UserListSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Register a new user account
    
    Create a new user with username, email, password and optional profile information.
    Returns user data and JWT tokens upon successful registration.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Show registration form in browsable API"""
        serializer = self.get_serializer()
        return Response({
            'message': 'User Registration Form',
            'fields': serializer.fields.keys()
        })
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)
        self.tokens = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }
        self.user_data = UserProfileSerializer(user).data
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            response.data = {
                "message": "User registered successfully",
                "user": self.user_data,
                "tokens": self.tokens
            }
        return response

class LoginView(generics.GenericAPIView):
    """
    User login endpoint
    
    Authenticate user with username and password.
    Returns user data and JWT tokens upon successful login.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Show login form in browsable API"""
        serializer = self.get_serializer()
        return Response({
            'message': 'User Login Form',
            'fields': ['username', 'password']
        })
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile management
    
    GET: Retrieve current user profile
    PUT/PATCH: Update current user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return User()
        return self.request.user
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.filter(id=self.request.user.id)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User management viewset (Admin only)
    
    Provides list and detail views for all users.
    Only accessible by admin users.
    """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserProfileSerializer
    
    @action(detail=True, methods=['post'])
    def make_staff(self, request, pk=None):
        """Make a user staff member"""
        user = self.get_object()
        user.is_staff = True
        user.save()
        return Response({'message': f'{user.username} is now a staff member'})
    
    @action(detail=True, methods=['post'])
    def remove_staff(self, request, pk=None):
        """Remove staff privileges from user"""
        user = self.get_object()
        if user.is_superuser:
            return Response(
                {'error': 'Cannot remove superuser privileges'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_staff = False
        user.save()
        return Response({'message': f'{user.username} is no longer a staff member'})
