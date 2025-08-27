from django.urls import path
from . import views

urlpatterns = [
    path('catalog/', views.quiz_catalog, name='quiz_catalog'),
    path('list/', views.quiz_list, name='quiz_list'),
    path('play/<int:quiz_id>/', views.quiz_play, name='quiz_play'),
    path('submit/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # URLs pour les enseignants
    path('upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('create-from-course/<int:course_id>/', views.create_quiz_from_course, name='create_quiz_from_course'),
    path('edit/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('participants/<int:quiz_id>/', views.quiz_participants, name='quiz_participants'),
    
    # URLs pour l'IA
    path('generate-suggestions/<int:quiz_id>/', views.generate_ai_suggestions, name='generate_ai_suggestions'),
    path('save-questions/<int:quiz_id>/', views.save_quiz_questions, name='save_quiz_questions'),
    path('publish/<int:quiz_id>/', views.publish_quiz, name='publish_quiz'),
    path('get-questions/<int:quiz_id>/', views.get_quiz_questions, name='get_quiz_questions'),
]
