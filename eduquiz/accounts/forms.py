from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, StudentProfile, TeacherProfile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    email = forms.EmailField(required=False, label="Email (optionnel pour les élèves)")
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True, label="Je suis")
    username = forms.CharField(
        max_length=150, 
        required=False, 
        label="Nom d'utilisateur (requis si pas d'email)",
        help_text="Utilisé pour se connecter. Requis si vous n'avez pas d'email."
    )
    class_name = forms.ChoiceField(
        choices=[('', 'Sélectionner une classe')] + User.CLASS_CHOICES,
        required=False,
        label="Classe (pour les élèves)",
        help_text="Sélectionnez votre classe si vous êtes élève"
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'user_type', 'class_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS aux champs
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary focus:border-primary'
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        class_name = cleaned_data.get('class_name')
        
        if user_type == 'teacher' and not email:
            raise ValidationError("L'email est obligatoire pour les enseignants.")
        
        if user_type == 'student':
            if not email and not username:
                raise ValidationError("Vous devez fournir soit un email, soit un nom d'utilisateur.")
            if not class_name:
                raise ValidationError("La classe est obligatoire pour les élèves.")
        
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        
        if username and User.objects.filter(username=username).exists():
            raise ValidationError("Ce nom d'utilisateur existe déjà.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get('email', '')
        username = self.cleaned_data.get('username', '')
        class_name = self.cleaned_data.get('class_name', '')
        
        if not username:
            if email:
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
            else:
                first_name = self.cleaned_data['first_name'].lower()
                last_name = self.cleaned_data['last_name'].lower()
                base_username = f"{first_name}.{last_name}"
                username = base_username
                counter = 1
                
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
        
        user.username = username
        user.email = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        if self.cleaned_data['user_type'] == 'student':
            user.class_name = class_name
        
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
