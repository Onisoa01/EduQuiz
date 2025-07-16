from django.urls import path
from . import views

urlpatterns = [
    path('catalog/', views.quiz_catalog, name='quiz_catalog'),
    path('play/<int:quiz_id>/', views.quiz_play, name='quiz_play'),
    path('submit/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # URLs pour les enseignants
    path('upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('edit/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
]
