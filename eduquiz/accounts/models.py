from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Élève'),
        ('teacher', 'Enseignant'),
    ]
    
    CLASS_CHOICES = [
        ('6eme', '6ème'),
        ('5eme', '5ème'),
        ('4eme', '4ème'),
        ('3eme', '3ème'),
        ('2nde', '2nde'),
        ('1ere', '1ère'),
        ('terminale', 'Terminale'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    level = models.CharField(max_length=20, blank=True, null=True)  # 6eme, 5eme, etc.
    class_name = models.CharField(max_length=20, choices=CLASS_CHOICES, blank=True, null=True, help_text="Classe de l'élève")
    points = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    email = models.EmailField(unique=True, blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_user_type_display()})"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    class_name = models.CharField(max_length=20, choices=User.CLASS_CHOICES, blank=True, null=True)
    favorite_subjects = models.JSONField(default=list, blank=True)
    learning_goals = models.TextField(blank=True)

    
    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.JSONField(default=list)  # Liste des matières enseignées
    classes = models.JSONField(default=list)   # Liste des classes
    school = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Profil enseignant de {self.user.get_full_name()}"
