from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from quiz.models import Quiz, QuizAttempt, Course
from gamification.models import UserBadge, Achievement

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
    
    # Quiz récents
    recent_attempts = QuizAttempt.objects.filter(
        user=request.user, 
        is_completed=True
    ).select_related('quiz').order_by('-completed_at')[:5]
    
    # Badges récents
    recent_badges = UserBadge.objects.filter(
        user=request.user
    ).select_related('badge').order_by('-earned_at')[:3]
    
    # Quiz recommandés
    recommended_quizzes = Quiz.objects.filter(
        is_published=True,
        level=request.user.level
    ).exclude(
        id__in=QuizAttempt.objects.filter(
            user=request.user, 
            is_completed=True
        ).values_list('quiz_id', flat=True)
    )[:3]
    
    # Performance par matière
    subject_performance = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True
    ).values('quiz__subject__name').annotate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    )
    
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
    
    # Statistiques de l'enseignant
    teacher_stats = {
        'total_courses': Course.objects.filter(teacher=request.user).count(),
        'total_quizzes': Quiz.objects.filter(course__teacher=request.user).count(),
        'active_students': QuizAttempt.objects.filter(
            quiz__course__teacher=request.user
        ).values('user').distinct().count(),
        'avg_success_rate': QuizAttempt.objects.filter(
            quiz__course__teacher=request.user,
            is_completed=True
        ).aggregate(avg_score=Avg('score'))['avg_score'] or 0,
    }
    
    # Cours récents
    recent_courses = Course.objects.filter(
        teacher=request.user
    ).order_by('-created_at')[:5]
    
    # Quiz en attente de validation
    pending_quizzes = Quiz.objects.filter(
        course__teacher=request.user,
        is_published=False
    )[:5]
    
    # Activité récente des étudiants
    recent_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=request.user,
        is_completed=True
    ).select_related('user', 'quiz').order_by('-completed_at')[:10]
    
    context = {
        'teacher_stats': teacher_stats,
        'recent_courses': recent_courses,
        'pending_quizzes': pending_quizzes,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'teacher/dashboard.html', context)
