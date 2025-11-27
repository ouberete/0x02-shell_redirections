# backend/core/views.py
from rest_framework import viewsets, permissions, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from .models import Level, SchoolClass, Student, User, Document
from .serializers import (
    LevelSerializer,
    SchoolClassSerializer,
    StudentSerializer,
    StudentCreateSerializer,
    ParentSerializer,
    DocumentSerializer
)

# =============================================================================
# API VIEWSETS
# =============================================================================

class LevelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows levels to be viewed or edited.
    """
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [permissions.IsAuthenticated] # Example permission

class SchoolClassViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows school classes to be viewed or edited.
    """
    queryset = SchoolClass.objects.select_related('level', 'academic_year', 'main_teacher').all()
    serializer_class = SchoolClassSerializer
    permission_classes = [permissions.IsAuthenticated]

class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for students.
    Handles both reading (display) and writing (create/update) with different serializers.
    """
    queryset = Student.objects.select_related('user', 'current_class').prefetch_related('parents').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Use StudentCreateSerializer for write actions (create, update),
        and StudentSerializer for read actions.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

class ParentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows parents/tutors to be viewed.
    Parents are typically created or linked when a student is created,
    so this endpoint is read-only for now.
    """
    queryset = User.objects.filter(role=User.Role.PARENT).prefetch_related('children')
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for document management.
    Allows uploading, listing, retrieving, and deleting documents.
    """
    queryset = Document.objects.select_related('user').all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser] # For file uploads

    def get_queryset(self):
        """
        Optionally filters the documents by user_id if a query parameter is provided.
        Admins can see all documents, other users can only see their own.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_staff: # Non-staff users can only see their own documents
            queryset = queryset.filter(user=user)

        user_id = self.request.query_params.get('user_id')
        if user_id and user.is_staff: # Staff can filter by user
            queryset = queryset.filter(user__id=user_id)

        return queryset

    def perform_create(self, serializer):
        """
        Associates the document with the user provided in the request body,
        or with the authenticated user if none is provided.
        """
        user = serializer.validated_data.get('user', self.request.user)
        # Check permissions: only admins/staff can upload for other users
        if user != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You do not have permission to upload documents for another user.")
        serializer.save(user=user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Custom action to download a specific document file.
        """
        document = self.get_object()
        try:
            # FileResponse handles setting the correct content-disposition header
            return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.filename)
        except FileNotFoundError:
            return Response({'error': 'File not found.'}, status=404)
