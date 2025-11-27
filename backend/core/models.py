# backend/core/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# =============================================================================
# 1. USER AND AUTHENTICATION MODELS
# =============================================================================

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Includes roles to manage permissions across the application.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        DIRECTOR = "DIRECTOR", _("Direction")
        ACCOUNTANT = "ACCOUNTANT", _("Comptable")
        TEACHER = "TEACHER", _("Professeur")
        PARENT = "PARENT", _("Parent")
        STUDENT = "STUDENT", _("Élève")

    role = models.CharField(_("Rôle"), max_length=50, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(_("Numéro de téléphone"), max_length=20, blank=True, null=True)
    address = models.TextField(_("Adresse"), blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.get_full_name() or self.username

# =============================================================================
# 2. ACADEMIC STRUCTURE MODELS
# =============================================================================

class AcademicYear(models.Model):
    """ Année Scolaire (ex: 2023-2024) """
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    is_current = models.BooleanField(_("Est l'année en cours"), default=False)

    def __str__(self):
        return f"{self.start_date.year}-{self.end_date.year}"

class Level(models.Model):
    """ Niveau (ex: Seconde, Première, Terminale) """
    name = models.CharField(_("Nom du niveau"), max_length=100, unique=True)

    def __str__(self):
        return self.name

class SchoolClass(models.Model):
    """ Classe (ex: Seconde A) """
    name = models.CharField(_("Nom de la classe"), max_length=100)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='classes', verbose_name=_("Niveau"))
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes', verbose_name=_("Année Scolaire"))
    main_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='main_classes', limit_choices_to={'role': User.Role.TEACHER}, verbose_name=_("Professeur principal"))

    class Meta:
        unique_together = ('name', 'academic_year')
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class Subject(models.Model):
    """ Matière (ex: Mathématiques) """
    name = models.CharField(_("Nom de la matière"), max_length=100, unique=True)
    coefficient = models.PositiveIntegerField(_("Coefficient"), default=1)

    def __str__(self):
        return self.name

# =============================================================================
# 3. PEOPLE MODELS (STUDENTS, PARENTS, TUTORS)
# =============================================================================

class Student(models.Model):
    """ Profil d'un élève """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile', limit_choices_to={'role': User.Role.STUDENT})
    registration_number = models.CharField(_("Matricule"), max_length=50, unique=True)
    date_of_birth = models.DateField(_("Date de naissance"))
    current_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name=_("Classe actuelle"))
    parents = models.ManyToManyField(User, related_name='children', limit_choices_to={'role': User.Role.PARENT}, verbose_name=_("Parents/Tuteurs"))

    def __str__(self):
        return self.user.get_full_name()

class Teacher(models.Model):
    """ Profil d'un professeur """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile', limit_choices_to={'role': User.Role.TEACHER})
    subjects = models.ManyToManyField(Subject, related_name='teachers', verbose_name=_("Matières enseignées"))
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name()

# =============================================================================
# 4. GRADING AND EVALUATION MODELS
# =============================================================================

class Term(models.Model):
    """ Trimestre ou Semestre """
    name = models.CharField(_("Nom"), max_length=50) # ex: Trimestre 1
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class Sequence(models.Model):
    """ Séquence d'évaluation """
    name = models.CharField(_("Nom"), max_length=50) # ex: Séquence 1
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='sequences')

    def __str__(self):
        return f"{self.name} - {self.term}"

class Grade(models.Model):
    """ Note d'un élève """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades', verbose_name=_("Élève"))
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades', verbose_name=_("Matière"))
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name='grades', verbose_name=_("Séquence"))
    score = models.DecimalField(_("Note"), max_digits=5, decimal_places=2)
    comment = models.TextField(_("Appréciation"), blank=True, null=True)

    class Meta:
        ordering = ['-sequence__term__academic_year', 'subject']

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.score}/20"

# =============================================================================
# 5. FINANCE AND PAYMENT MODELS
# =============================================================================

class FeeType(models.Model):
    """ Type de frais (ex: Scolarité, Inscription) """
    name = models.CharField(_("Nom du frais"), max_length=150)
    amount = models.DecimalField(_("Montant"), max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"

class Invoice(models.Model):
    """ Facture pour un élève """
    class Status(models.TextChoices):
        UNPAID = "UNPAID", _("Impayée")
        PAID = "PAID", _("Payée")
        PARTIALLY_PAID = "PARTIALLY_PAID", _("Partiellement Payée")
        CANCELLED = "CANCELLED", _("Annulée")

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='invoices')
    total_amount = models.DecimalField(_("Montant total"), max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(_("Montant payé"), max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(_("Date d'échéance"))
    status = models.CharField(_("Statut"), max_length=20, choices=Status.choices, default=Status.UNPAID)

    def __str__(self):
        return f"Facture #{self.id} pour {self.student}"

class InvoiceItem(models.Model):
    """ Ligne d'une facture """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT)
    description = models.CharField(_("Description"), max_length=255)
    amount = models.DecimalField(_("Montant"), max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description} ({self.amount})"

class Payment(models.Model):
    """ Paiement effectué """
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", _("Espèces")
        BANK_TRANSFER = "BANK_TRANSFER", _("Virement Bancaire")
        MOBILE_MONEY = "MOBILE_MONEY", _("Mobile Money")
        CARD = "CARD", _("Carte Bancaire")

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_("Montant"), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_("Date de paiement"), auto_now_add=True)
    payment_method = models.CharField(_("Moyen de paiement"), max_length=20, choices=PaymentMethod.choices)

    def __str__(self):
        return f"Paiement de {self.amount} pour la facture #{self.invoice.id}"
