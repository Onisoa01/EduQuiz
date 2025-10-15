from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from .forms import CustomUserCreationForm, StudentProfileForm, TeacherProfileForm
from .models import User, StudentProfile, TeacherProfile
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        print(f"User type: {self.request.user.user_type}")
        
        if self.request.user.user_type == 'admin':
            return reverse_lazy('admin_dashboard')
        elif self.request.user.user_type == 'teacher':
            return reverse_lazy('teacher_dashboard')
        else:
            return reverse_lazy('student_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bienvenue {form.get_user().first_name}!')
        return super().form_valid(form)

# def register_view(request): ...

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard principal de l'administrateur"""
    students = User.objects.filter(user_type='student').order_by('-date_joined')
    teachers = User.objects.filter(user_type='teacher').order_by('-date_joined')
    
    context = {
        'total_students': students.count(),
        'total_teachers': teachers.count(),
        'recent_students': students[:5],
        'recent_teachers': teachers[:5],
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users_list(request):
    """Liste de tous les utilisateurs"""
    user_type = request.GET.get('type', 'all')
    
    if user_type == 'student':
        users = User.objects.filter(user_type='student')
    elif user_type == 'teacher':
        users = User.objects.filter(user_type='teacher')
    else:
        users = User.objects.exclude(user_type='admin')
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'user_type': user_type,
    }
    return render(request, 'admin/users_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_create_user(request):
    """Créer un nouvel utilisateur (étudiant ou enseignant)"""
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        class_name = request.POST.get('class_name', '')
        
        try:
            with transaction.atomic():
                # Créer l'utilisateur
                user = User.objects.create_user(
                    username=username,
                    email=email if email else None,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type,
                    class_name=class_name if user_type == 'student' else None
                )
                
                # Créer le profil correspondant
                if user_type == 'student':
                    StudentProfile.objects.create(user=user)
                else:
                    TeacherProfile.objects.create(user=user)
                
                messages.success(request, f'Utilisateur {user.get_full_name()} créé avec succès!')
                return redirect('admin_users_list')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    return render(request, 'admin/create_user.html')

@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    """Modifier un utilisateur existant"""
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email', '')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        
        if user.user_type == 'student':
            user.class_name = request.POST.get('class_name')
        
        # Changer le mot de passe si fourni
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        messages.success(request, 'Utilisateur modifié avec succès!')
        return redirect('admin_users_list')
    
    context = {'user_to_edit': user}
    return render(request, 'admin/edit_user.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_delete_user(request, user_id):
    """Supprimer un utilisateur"""
    try:
        user = User.objects.get(id=user_id)
        if user.user_type == 'admin':
            return JsonResponse({'success': False, 'error': 'Impossible de supprimer un administrateur'})
        
        user.delete()
        messages.success(request, 'Utilisateur supprimé avec succès!')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
