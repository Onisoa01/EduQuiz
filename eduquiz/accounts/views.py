from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from .forms import CustomUserCreationForm, StudentProfileForm, TeacherProfileForm
from .models import User, StudentProfile, TeacherProfile

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        # Debug: afficher le type d'utilisateur
        print(f"User type: {self.request.user.user_type}")
        
        if self.request.user.user_type == 'teacher':
            return reverse_lazy('teacher_dashboard')
        else:
            return reverse_lazy('student_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bienvenue {form.get_user().first_name}!')
        return super().form_valid(form)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Debug: afficher les informations de l'utilisateur créé
                    print(f"User created: {user.username} ({user.email}), type: {user.user_type}")
                    
                    # Créer le profil correspondant
                    if user.user_type == 'student':
                        StudentProfile.objects.create(user=user)
                        print("Student profile created")
                    else:
                        TeacherProfile.objects.create(user=user)
                        print("Teacher profile created")
                    
                    login(request, user)
                    messages.success(request, 'Compte créé avec succès!')
                    
                    # Rediriger selon le type d'utilisateur
                    if user.user_type == 'teacher':
                        return redirect('teacher_dashboard')
                    else:
                        return redirect('student_dashboard')
                        
            except Exception as e:
                print(f"Error during registration: {e}")
                messages.error(request, 'Une erreur est survenue lors de la création du compte. Veuillez réessayer.')
        else:
            # Debug: afficher les erreurs du formulaire
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

@login_required
def profile_view(request):
    user = request.user
    
    if user.user_type == 'student':
        profile, created = StudentProfile.objects.get_or_create(user=user)
        if request.method == 'POST':
            form = StudentProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil mis à jour!')
                return redirect('profile')
        else:
            form = StudentProfileForm(instance=profile)
    else:
        profile, created = TeacherProfile.objects.get_or_create(user=user)
        if request.method == 'POST':
            form = TeacherProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil mis à jour!')
                return redirect('profile')
        else:
            form = TeacherProfileForm(instance=profile)
    
    return render(request, 'student/profile.html', {
        'form': form,
        'profile': profile
    })
