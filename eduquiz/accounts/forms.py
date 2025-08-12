from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, StudentProfile, TeacherProfile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Email")
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True, label="Je suis")
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS aux champs
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        return email
    
    def clean_username(self):
        # Cette méthode ne sera pas appelée car nous ne demandons pas le username
        # mais nous la gardons pour éviter les erreurs
        return self.cleaned_data.get('username', '')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        
        # Générer un username unique basé sur l'email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        # S'assurer que le username est unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        user.email = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        
        if commit:
            user.save()
        return user

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_name', 'learning_goals']
        widgets = {
            'class_name': forms.Select(choices=[
                ('', 'Sélectionner une classe'),
                ('6eme', '6ème'),
                ('5eme', '5ème'),
                ('4eme', '4ème'),
                ('3eme', '3ème'),
                ('seconde', 'Seconde'),
                ('premiere', 'Première'),
                ('terminale', 'Terminale'),
            ], attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'learning_goals': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'placeholder': 'Décrivez vos objectifs d\'apprentissage...'
            }),
        }
        labels = {
            'class_name': 'Classe',
            'learning_goals': 'Objectifs d\'apprentissage',
        }

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['school']
        widgets = {
            'school': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'placeholder': 'Nom de votre établissement...'
            }),
        }
        labels = {
            'school': 'Établissement',
        }
