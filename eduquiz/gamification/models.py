from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Badge(models.Model):
    BADGE_TYPES = [
        ('achievement', 'Réussite'),
        ('streak', 'Série'),
        ('mastery', 'Maîtrise'),
        ('participation', 'Participation'),
        ('speed', 'Vitesse'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-medal')
    color = models.CharField(max_length=20, default='gold')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    points_required = models.IntegerField(default=0)
    condition = models.JSONField(default=dict)  # Conditions spécifiques pour obtenir le badge
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.badge.name}"

class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    points_earned = models.IntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

class Leaderboard(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('all_time', 'Tout temps'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    points = models.IntegerField()
    rank = models.IntegerField()
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    class Meta:
        unique_together = ['user', 'period', 'period_start']
        ordering = ['rank']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Rang {self.rank} ({self.get_period_display()})"
