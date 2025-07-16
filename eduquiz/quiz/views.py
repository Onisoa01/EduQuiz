from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from .models import Quiz, Question, QuizAttempt, Answer, Course, Subject
from .forms import CourseUploadForm, QuizForm, QuestionForm, ChoiceFormSet
import json

def quiz_catalog(request):
    """Affiche le catalogue des quiz avec filtres"""
    quizzes = Quiz.objects.filter(is_published=True).select_related('subject')
    subjects = Subject.objects.all()
    
    # Filtres
    subject_filter = request.GET.get('subject')
    level_filter = request.GET.get('level')
    difficulty_filter = request.GET.get('difficulty')
    search = request.GET.get('search')
    
    if subject_filter:
        quizzes = quizzes.filter(subject__slug=subject_filter)
    if level_filter:
        quizzes = quizzes.filter(level=level_filter)
    if difficulty_filter:
        quizzes = quizzes.filter(difficulty=difficulty_filter)
    if search:
        quizzes = quizzes.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Ajouter les statistiques pour chaque quiz
    for quiz in quizzes:
        quiz.participants_count = QuizAttempt.objects.filter(quiz=quiz, is_completed=True).count()
    
    context = {
        'quizzes': quizzes,
        'subjects': subjects,
        'current_filters': {
            'subject': subject_filter,
            'level': level_filter,
            'difficulty': difficulty_filter,
            'search': search,
        }
    }
    return render(request, 'quiz/catalog.html', context)

@login_required
def quiz_play(request, quiz_id):
    """Interface de jeu du quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    # Créer ou récupérer une tentative
    attempt, created = QuizAttempt.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        is_completed=False,
        defaults={'total_points': sum(q.points for q in quiz.questions.all())}
    )
    
    questions = quiz.questions.prefetch_related('choices').all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'attempt': attempt,
    }
    return render(request, 'quiz/play.html', context)

@login_required
def submit_quiz(request, quiz_id):
    """Soumission des réponses du quiz"""
    if request.method != 'POST':
        return redirect('quiz_play', quiz_id=quiz_id)
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(QuizAttempt, user=request.user, quiz=quiz, is_completed=False)
    
    # Traiter les réponses
    total_score = 0
    answers_data = json.loads(request.body)
    
    for question_id, answer_data in answers_data.items():
        question = get_object_or_404(Question, id=question_id, quiz=quiz)
        
        answer = Answer.objects.create(
            attempt=attempt,
            question=question
        )
        
        if question.question_type == 'mcq':
            choice_id = answer_data.get('choice_id')
            if choice_id:
                choice = get_object_or_404(Choice, id=choice_id, question=question)
                answer.selected_choice = choice
                if choice.is_correct:
                    answer.is_correct = True
                    answer.points_earned = question.points
                    total_score += question.points
        
        elif question.question_type == 'open':
            answer.open_answer = answer_data.get('text', '')
            # TODO: Intégrer l'IA pour évaluer les réponses ouvertes
        
        answer.save()
    
    # Finaliser la tentative
    attempt.score = total_score
    attempt.completed_at = timezone.now()
    attempt.time_taken = attempt.completed_at - attempt.started_at
    attempt.is_completed = True
    attempt.save()
    
    # Mettre à jour les points de l'utilisateur
    request.user.points += total_score
    request.user.xp += total_score
    request.user.save()
    
    return JsonResponse({'success': True, 'attempt_id': attempt.id})

@login_required
def quiz_results(request, attempt_id):
    """Affichage des résultats du quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user, is_completed=True)
    answers = attempt.answers.select_related('question', 'selected_choice').all()
    
    context = {
        'attempt': attempt,
        'answers': answers,
        'quiz': attempt.quiz,
    }
    return render(request, 'quiz/results.html', context)

# Vues pour les enseignants
@login_required
def upload_pdf(request):
    """Téléversement de PDF par les enseignants"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            
            # TODO: Déclencher le traitement IA du PDF
            messages.success(request, "PDF téléversé avec succès! L'analyse IA va commencer.")
            return redirect('teacher_dashboard')
    else:
        form = CourseUploadForm()
    
    return render(request, 'teacher/upload_pdf.html', {'form': form})

@login_required
def create_quiz(request):
    """Création manuelle de quiz par les enseignants"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            # Associer à un cours existant ou créer un cours temporaire
            quiz.save()
            messages.success(request, "Quiz créé avec succès!")
            return redirect('edit_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'teacher/create_quiz.html', {'form': form})

@login_required
def edit_quiz(request, quiz_id):
    """Édition d'un quiz et de ses questions"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    questions = quiz.questions.prefetch_related('choices').all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'teacher/edit_quiz.html', context)
