# backend/core/views.py
from rest_framework import viewsets, permissions
from .models import Level, SchoolClass, Student, User
from .serializers import (
    LevelSerializer,
    SchoolClassSerializer,
    StudentSerializer,
    StudentCreateSerializer,
    ParentSerializer
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
