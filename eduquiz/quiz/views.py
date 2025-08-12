from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import Quiz, Question, QuizAttempt, Answer, Course, Subject, Choice
from .forms import CourseUploadForm, QuizForm, QuestionForm, ChoiceFormSet
from ai_service.gemini_service import GeminiService

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
def quiz_list(request):
    """Liste des quiz pour les enseignants"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    # Récupérer les quiz de l'enseignant
    quizzes = Quiz.objects.filter(course__teacher=request.user).select_related('subject', 'course')
    
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'teacher/quiz_list.html', context)

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
            
            messages.success(request, "PDF téléversé avec succès! Vous pouvez maintenant créer des quiz basés sur ce cours.")
            return redirect('create_quiz_from_course', course_id=course.id)
    else:
        form = CourseUploadForm()
    
    return render(request, 'teacher/upload_pdf.html', {'form': form})

@login_required
def create_quiz_from_course(request, course_id):
    """Créer un quiz à partir d'un cours téléversé"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.subject = course.subject
            quiz.level = course.level
            quiz.save()
            
            messages.success(request, "Quiz créé avec succès! Vous pouvez maintenant utiliser l'IA pour générer des questions.")
            return redirect('edit_quiz', quiz_id=quiz.id)
    else:
        # Pré-remplir le formulaire avec les données du cours
        initial_data = {
            'title': f"Quiz - {course.title}",
            'description': course.description,
        }
        form = QuizForm(initial=initial_data)
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'teacher/create_quiz_from_course.html', context)

@login_required
def edit_quiz(request, quiz_id):
    """Édition d'un quiz et de ses questions avec suggestions IA"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    questions = quiz.questions.prefetch_related('choices').all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'course': quiz.course,
    }
    return render(request, 'teacher/edit_quiz.html', context)

@login_required
@require_http_methods(["POST"])
def generate_ai_suggestions(request, quiz_id):
    """Générer des suggestions de questions avec l'IA"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    
    try:
        data = json.loads(request.body)
        num_questions = data.get('num_questions', 15)
        
        # Initialiser le service Gemini
        gemini_service = GeminiService()
        
        # Extraire le texte du PDF
        pdf_content = gemini_service.extract_text_from_pdf(quiz.course.pdf_file)
        
        if not pdf_content:
            return JsonResponse({
                'success': False, 
                'error': 'Impossible d\'extraire le contenu du PDF'
            })
        
        # Générer les suggestions
        result = gemini_service.analyze_pdf_and_suggest_quiz(
            pdf_content=pdf_content,
            subject=quiz.subject.name,
            level=quiz.level,
            num_questions=num_questions
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'suggestions': result['data']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def save_quiz_questions(request, quiz_id):
    """Sauvegarder les questions validées par l'enseignant"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    
    try:
        data = json.loads(request.body)
        questions_data = data.get('questions', [])
        
        # Supprimer les anciennes questions
        quiz.questions.all().delete()
        
        # Créer les nouvelles questions
        for i, question_data in enumerate(questions_data):
            question = Question.objects.create(
                quiz=quiz,
                question_text=question_data['question_text'],
                question_type=question_data['question_type'],
                points=question_data.get('points', 5),
                explanation=question_data.get('explanation', ''),
                order=i + 1
            )
            
            # Créer les choix pour les QCM
            if question_data['question_type'] == 'mcq' and 'choices' in question_data:
                for j, choice_data in enumerate(question_data['choices']):
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_data['text'],
                        is_correct=choice_data['is_correct'],
                        order=j + 1
                    )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la sauvegarde: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def publish_quiz(request, quiz_id):
    """Publier un quiz"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    
    if quiz.questions.count() == 0:
        return JsonResponse({
            'success': False,
            'error': 'Impossible de publier un quiz sans questions'
        })
    
    quiz.is_published = True
    quiz.save()
    
    return JsonResponse({'success': True})

@login_required
def create_quiz(request):
    """Création manuelle de quiz par les enseignants"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    # Rediriger vers l'upload de PDF d'abord
    messages.info(request, "Pour créer un quiz, commencez par téléverser le support de cours (PDF).")
    return redirect('upload_pdf')
