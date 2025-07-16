from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .models import Badge, UserBadge, Leaderboard
from accounts.models import User

@login_required
def leaderboard_view(request):
    """Affichage du classement"""
    period = request.GET.get('period', 'all_time')
    scope = request.GET.get('scope', 'global')  # global, class, level
    
    # Récupérer les utilisateurs avec leurs points
    users = User.objects.filter(user_type='student').order_by('-points')[:50]
    
    # Ajouter le rang de l'utilisateur actuel
    current_user_rank = None
    if request.user.user_type == 'student':
        users_above = User.objects.filter(
            user_type='student', 
            points__gt=request.user.points
        ).count()
        current_user_rank = users_above + 1
    
    context = {
        'users': users,
        'current_user_rank': current_user_rank,
        'current_period': period,
        'current_scope': scope,
    }
    return render(request, 'leaderboard.html', context)

@login_required
def badges_view(request):
    """Affichage des badges de l'utilisateur"""
    user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    available_badges = Badge.objects.filter(is_active=True)
    
    context = {
        'user_badges': user_badges,
        'available_badges': available_badges,
    }
    return render(request, 'gamification/badges.html', context)
