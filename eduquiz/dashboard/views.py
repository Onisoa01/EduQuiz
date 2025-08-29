from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Q, F
from quiz.models import Quiz, QuizAttempt, Course, Subject
from gamification.models import UserBadge, Achievement
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator

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
    successful_attempts = user_attempts.filter(score__gte=F('total_points') * 0.5)
    
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
    
    for attempt in recent_attempts:
        if attempt.total_points > 0:
            attempt.percentage = (attempt.score / attempt.total_points) * 100
            attempt.is_passing = attempt.percentage >= 50
        else:
            attempt.percentage = 0
            attempt.is_passing = False
    
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
            total_score = subject_attempts.aggregate(total_score=Sum('score'))['total_score'] or 0
            total_possible = subject_attempts.aggregate(total_possible=Sum('total_points'))['total_possible'] or 1
            avg_percentage = (total_score / total_possible) * 100 if total_possible > 0 else 0
            
            subject_performance.append({
                'subject': subject,
                'avg_score': round(avg_percentage, 1),
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
    
    # Get all courses and quizzes created by this teacher
    teacher_courses = Course.objects.filter(teacher=request.user)
    teacher_quizzes = Quiz.objects.filter(course__teacher=request.user).select_related('subject', 'course')
    published_quizzes = teacher_quizzes.filter(is_published=True)
    draft_quizzes = teacher_quizzes.filter(is_published=False)
    
    # Get all attempts on teacher's quizzes
    all_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=request.user,
        is_completed=True
    ).select_related('user', 'quiz')
    
    # Calculate teacher statistics
    teacher_stats = {
        'total_courses': teacher_courses.count(),
        'total_quizzes': teacher_quizzes.count(),
        'published_quizzes': published_quizzes.count(),
        'total_attempts': all_attempts.count(),
    }
    
    recent_attempts_list = all_attempts.order_by('-completed_at')
    paginator = Paginator(recent_attempts_list, 5)  # Show 5 attempts per page
    page_number = request.GET.get('page')
    recent_attempts = paginator.get_page(page_number)
    
    # Calculate weekly statistics
    one_week_ago = timezone.now() - timedelta(days=7)
    weekly_attempts = all_attempts.filter(completed_at__gte=one_week_ago)
    
    # Get unique students who attempted quizzes this week
    weekly_students = weekly_attempts.values('user').distinct().count()
    
    # Calculate average score for the week
    weekly_avg_score = 0
    if weekly_attempts.exists():
        total_score = weekly_attempts.aggregate(total=Sum('score'))['total'] or 0
        total_possible = weekly_attempts.aggregate(total=Sum('total_points'))['total'] or 1
        weekly_avg_score = (total_score / total_possible) * 100 if total_possible > 0 else 0
    
    weekly_stats = {
        'completed_attempts': weekly_attempts.count(),
        'avg_score': round(weekly_avg_score, 1),
        'new_students': weekly_students,
    }
    
    context = {
        'teacher_stats': teacher_stats,
        'teacher_quizzes': teacher_quizzes.order_by('-created_at'),
        'draft_quizzes': draft_quizzes.order_by('-created_at')[:5],
        'recent_attempts': recent_attempts,  # Now paginated
        'weekly_stats': weekly_stats,
    }
    return render(request, 'teacher/dashboard.html', context)
