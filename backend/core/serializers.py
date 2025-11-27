# backend/core/serializers.py
from rest_framework import serializers
from .models import User, Student, Level, SchoolClass, AcademicYear, Teacher

# =============================================================================
# USER SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """ Serializer pour le modèle User, utilisé pour l'affichage """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 'role_display', 'phone_number', 'address')
        read_only_fields = ('role', 'role_display') # Le rôle est géré par la logique métier

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de nouveaux utilisateurs.
    Sépare la création (avec mot de passe) de la mise à jour.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'email', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            role=validated_data.get('role', User.Role.STUDENT)
        )
        return user

# =============================================================================
# ACADEMIC STRUCTURE SERIALIZERS
# =============================================================================

class LevelSerializer(serializers.ModelSerializer):
    """ Serializer pour le modèle Level """
    class Meta:
        model = Level
        fields = '__all__'

class SchoolClassSerializer(serializers.ModelSerializer):
    """ Serializer pour le modèle SchoolClass """
    level_name = serializers.CharField(source='level.name', read_only=True)
    academic_year = serializers.StringRelatedField(read_only=True)
    main_teacher_name = serializers.CharField(source='main_teacher.get_full_name', read_only=True, default=None)

    class Meta:
        model = SchoolClass
        fields = ('id', 'name', 'level', 'level_name', 'academic_year', 'main_teacher', 'main_teacher_name')

# =============================================================================
# PEOPLE SERIALIZERS (STUDENT, PARENT)
# =============================================================================

class StudentSerializer(serializers.ModelSerializer):
    """ Serializer complet pour le modèle Student """
    user = UserSerializer()
    current_class_name = serializers.CharField(source='current_class.name', read_only=True, default=None)
    parents = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = (
            'user', 'registration_number', 'date_of_birth',
            'current_class', 'current_class_name', 'parents'
        )

class StudentCreateSerializer(serializers.ModelSerializer):
    """ Serializer pour la création et la mise à jour d'un élève """
    user = UserRegistrationSerializer()

    class Meta:
        model = Student
        fields = ('user', 'registration_number', 'date_of_birth', 'current_class', 'parents')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = User.Role.STUDENT # Forcer le rôle

        # Création de l'utilisateur
        user_serializer = UserRegistrationSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Création de l'élève
        student = Student.objects.create(user=user, **validated_data)
        return student

class ParentSerializer(UserSerializer):
    """ Serializer pour les parents, hérite de UserSerializer """
    children = StudentSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('children',)
