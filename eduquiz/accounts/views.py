from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, StudentProfileForm, TeacherProfileForm
from .models import User, StudentProfile, TeacherProfile

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        if self.request.user.user_type == 'teacher':
            return '/dashboard/teacher/'
        else:
            return '/dashboard/student/'

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Créer le profil correspondant
            if user.user_type == 'student':
                StudentProfile.objects.create(user=user)
            else:
                TeacherProfile.objects.create(user=user)
            
            login(request, user)
            messages.success(request, 'Compte créé avec succès!')
            
            # Rediriger selon le type d'utilisateur
            if user.user_type == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
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
