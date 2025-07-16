from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, TeacherProfile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS aux champs
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_name', 'learning_goals']
        widgets = {
            'class_name': forms.Select(choices=[
                ('6eme', '6ème'),
                ('5eme', '5ème'),
                ('4eme', '4ème'),
                ('3eme', '3ème'),
                ('seconde', 'Seconde'),
                ('premiere', 'Première'),
                ('terminale', 'Terminale'),
            ]),
            'learning_goals': forms.Textarea(attrs={'rows': 3}),
        }

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['school']
        widgets = {
            'school': forms.TextInput(),
        }
