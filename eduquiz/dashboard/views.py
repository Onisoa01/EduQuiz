from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from quiz.models import Quiz, QuizAttempt, Course
from gamification.models import UserBadge, Achievement

@login_required
def dashboard_redirect(request):
    """Redirection automatique vers le bon dashboard"""
    if request.user.user_type == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def student_dashboard(request):
    """Tableau de bord étudiant"""
    if request.user.user_type != 'student':
        return redirect('teacher_dashboard')
    
    # Statistiques de l'utilisateur
    user_stats = {
        'total_points': request.user.points,
        'current_level': request.user.current_level,
        'xp': request.user.xp,
        'streak_days': request.user.streak_days,
    }
    
    # Quiz récents (simulés pour le moment)
    recent_attempts = []
    
    # Badges récents (simulés pour le moment)
    recent_badges = []
    
    # Quiz recommandés (simulés pour le moment)
    recommended_quizzes = []
    
    # Performance par matière (simulée pour le moment)
    subject_performance = []
    
    context = {
        'user_stats': user_stats,
        'recent_attempts': recent_attempts,
        'recent_badges': recent_badges,
        'recommended_quizzes': recommended_quizzes,
        'subject_performance': subject_performance,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Tableau de bord enseignant"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')
    
    # Statistiques de l'enseignant (simulées pour le moment)
    teacher_stats = {
        'total_courses': 0,
        'total_quizzes': 0,
        'active_students': 0,
        'avg_success_rate': 0,
    }
    
    # Cours récents (simulés pour le moment)
    recent_courses = []
    
    # Quiz en attente de validation (simulés pour le moment)
    pending_quizzes = []
    
    # Activité récente des étudiants (simulée pour le moment)
    recent_attempts = []
    
    context = {
        'teacher_stats': teacher_stats,
        'recent_courses': recent_courses,
        'pending_quizzes': pending_quizzes,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'teacher/dashboard.html', context)
