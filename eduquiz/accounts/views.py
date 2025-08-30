from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views import View
import time
import random
from .forms import CustomUserCreationForm, StudentProfileForm, TeacherProfileForm
from .models import User, StudentProfile, TeacherProfile

@method_decorator(never_cache, name='dispatch')
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
        response = super().form_valid(form)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

@never_cache
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = None
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
                
                if user:
                    login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
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
    
    response = render(request, 'auth/register.html', {'form': form})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
@never_cache
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

@method_decorator(never_cache, name='dispatch')
class CustomLogoutView(View):
    """
    Custom logout view that properly clears sessions and prevents caching issues
    """
    
    def get(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def post(self, request, *args, **kwargs):
        return self.logout_user(request)
    
    def logout_user(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            pass  # This consumes all messages
        storage.used = True
        
        if hasattr(request, 'session'):
            # Clear all session keys individually
            session_keys = list(request.session.keys())
            for key in session_keys:
                del request.session[key]
            
            # Force session flush and regenerate session key
            request.session.flush()
            request.session.cycle_key()
        
        if hasattr(request, 'user'):
            request.user = None
        
        # Logout the user
        logout(request)
        
        timestamp = int(time.time())
        random_id = random.randint(1000, 9999)
        redirect_url = f"/?_logout={timestamp}&_clear={random_id}&_nocache=1"
        
        # Create response with strict cache control headers
        response = HttpResponseRedirect(redirect_url)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        response['Last-Modified'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        response['If-Modified-Since'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        response['Vary'] = 'Cookie'
        
        response.delete_cookie('sessionid', path='/', domain=None)
        response.delete_cookie('csrftoken', path='/', domain=None)
        
        # Clear any custom cookies that might store user state
        response.delete_cookie('user_type', path='/', domain=None)
        response.delete_cookie('user_id', path='/', domain=None)
        
        return response

@never_cache
def validate_session(request):
    """
    API endpoint to validate if user session is still active
    Used by JavaScript to check authentication state periodically
    """
    if request.user.is_authenticated and request.user.is_active:
        return JsonResponse({
            'authenticated': True,
            'user_type': request.user.user_type,
            'username': request.user.username
        })
    else:
        response = JsonResponse({'authenticated': False}, status=401)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
