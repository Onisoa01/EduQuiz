from django import forms
from .models import Course, Quiz, Question, Choice

class CourseUploadForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'subject', 'level', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'placeholder': 'Ex: Les triangles et leurs propriétés'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'rows': 3,
                'placeholder': 'Décrivez brièvement le contenu de ce cours...'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'level': forms.Select(choices=[
                ('6eme', '6ème'),
                ('5eme', '5ème'),
                ('4eme', '4ème'),
                ('3eme', '3ème'),
                ('seconde', 'Seconde'),
                ('premiere', 'Première'),
                ('terminale', 'Terminale'),
            ], attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': '.pdf'
            }),
        }

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'difficulty', 'time_limit', 'points_reward']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'rows': 3
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'min': 1,
                'max': 120
            }),
            'points_reward': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'min': 10,
                'max': 200
            }),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'points', 'explanation']
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'rows': 3
            }),
            'question_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'min': 1,
                'max': 20
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary',
                'rows': 2
            }),
        }

# Formset pour gérer plusieurs choix
ChoiceFormSet = forms.inlineformset_factory(
    Question, 
    Choice, 
    fields=['choice_text', 'is_correct'], 
    extra=4, 
    max_num=4,
    widgets={
        'choice_text': forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary focus:border-primary'
        }),
        'is_correct': forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
        }),
    }
)
