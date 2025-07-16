from django.contrib import admin
from .models import Subject, Course, Quiz, Question, Choice, QuizAttempt, Answer

admin.site.register(Subject)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(QuizAttempt)
admin.site.register(Answer)