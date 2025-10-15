from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Q
from quiz.models import Quiz, QuizAttempt, Course, Subject
from gamification.models import UserBadge, Achievement
from django.utils import timezone
from datetime import timedelta

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
    
    user_attempts = QuizAttempt.objects.filter(user=request.user)
    successful_attempts = user_attempts.filter(score__gte=50)  # 50% ou plus = réussi
    
    current_level = request.user.current_level
    xp_needed = (current_level + 1) * 200  # Each level needs 200 more XP than previous
    progress_percent = min((request.user.xp / xp_needed) * 100, 100) if xp_needed > 0 else 0
    
    user_stats = {
        'total_points': request.user.points,
        'current_level': current_level,
        'xp': request.user.xp,
        'xp_needed': xp_needed,
        'progress_percent': round(progress_percent, 1),
        'streak_days': request.user.streak_days,
        'total_attempts': user_attempts.count(),
        'successful_attempts': successful_attempts.count(),
        'total_badges': UserBadge.objects.filter(user=request.user).count(),
    }
    
    recent_attempts = user_attempts.select_related('quiz', 'quiz__subject').order_by('-completed_at')[:5]
    
    recent_badges = UserBadge.objects.filter(user=request.user).select_related('badge').order_by('-earned_at')[:3]
    
    available_quizzes = Quiz.objects.filter(
        is_published=True,
        level=request.user.class_name
    ).exclude(
        id__in=user_attempts.values_list('quiz_id', flat=True)
    ).select_related('subject')[:5]
    
    subject_performance = []
    subjects = Subject.objects.all()
    for subject in subjects:
        subject_attempts = user_attempts.filter(quiz__subject=subject)
        if subject_attempts.exists():
            avg_score = subject_attempts.aggregate(avg_score=Avg('score'))['avg_score']
            subject_performance.append({
                'subject': subject,
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'attempts_count': subject_attempts.count()
            })
    
    class_leaderboard = []
    if request.user.class_name:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        class_students = User.objects.filter(
            user_type='student',
            class_name=request.user.class_name
        ).order_by('-points')[:10]
        
        for i, student in enumerate(class_students, 1):
            class_leaderboard.append({
                'rank': i,
                'user': student,
                'points': student.points,
                'is_current_user': student == request.user
            })
    
    today = timezone.now().date()
    quiz_of_the_day = Quiz.objects.filter(
        is_published=True,
        level=request.user.class_name,
        created_at__date=today
    ).first()
    
    if not quiz_of_the_day:
        # Fallback to most recent quiz for the class
        quiz_of_the_day = Quiz.objects.filter(
            is_published=True,
            level=request.user.class_name
        ).order_by('-created_at').first()
    
    context = {
        'user_stats': user_stats,
        'recent_attempts': recent_attempts,
        'recent_badges': recent_badges,
        'available_quizzes': available_quizzes,
        'subject_performance': subject_performance,
        'class_leaderboard': class_leaderboard,
        'quiz_of_the_day': quiz_of_the_day,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Tableau de bord enseignant"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')
    
    teacher_courses = Course.objects.filter(teacher=request.user)
    teacher_quizzes = Quiz.objects.filter(course__teacher=request.user).select_related('subject', 'course')
    
    teacher_stats = {
        'total_courses': teacher_courses.count(),
        'total_quizzes': teacher_quizzes.count(),
        'published_quizzes': teacher_quizzes.filter(is_published=True).count(),
        'total_attempts': QuizAttempt.objects.filter(quiz__course__teacher=request.user, is_completed=True).count(),
    }
    
    draft_quizzes = teacher_quizzes.filter(is_published=False).prefetch_related('questions')[:5]
    
    recent_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=request.user,
        is_completed=True
    ).select_related('user', 'quiz').order_by('-completed_at')[:10]
    
    week_ago = timezone.now() - timedelta(days=7)
    weekly_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=request.user,
        is_completed=True,
        completed_at__gte=week_ago
    )
    
    weekly_stats = {
        'completed_attempts': weekly_attempts.count(),
        'avg_score': weekly_attempts.aggregate(avg=Avg('score'))['avg'] or 0,
        'new_students': 0,  # TODO: Implement student tracking
    }
    
    context = {
        'teacher_stats': teacher_stats,
        'teacher_quizzes': teacher_quizzes[:10],  # Show first 10 quizzes
        'draft_quizzes': draft_quizzes,
        'recent_attempts': recent_attempts,
        'weekly_stats': weekly_stats,
    }
    return render(request, 'teacher/dashboard.html', context)
