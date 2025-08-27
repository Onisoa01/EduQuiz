from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import Quiz, Question, QuizAttempt, Answer, Course, Subject, Choice
from .forms import CourseUploadForm, QuizForm, QuestionForm, ChoiceFormSet
from ai_service.gemini_service import GeminiService

def quiz_catalog(request):
    """Affiche le catalogue des quiz avec filtres"""
    if request.user.is_authenticated and hasattr(request.user, 'user_type') and request.user.user_type == 'student':
        if hasattr(request.user, 'class_name') and request.user.class_name:
            quizzes = Quiz.objects.filter(is_published=True, level=request.user.class_name).select_related('subject')
        else:
            quizzes = Quiz.objects.none()  # No quizzes if no class assigned
    else:
        quizzes = Quiz.objects.filter(is_published=True).select_related('subject')
    
    subjects = Subject.objects.all()
    
    search = request.GET.get('search')
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
            'search': search,
        }
    }
    return render(request, 'quiz/catalog.html', context)

@login_required
def quiz_list(request):
    """Liste des quiz pour les enseignants avec participants et scores"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    quizzes = Quiz.objects.filter(course__teacher=request.user).select_related('subject', 'course').prefetch_related('quizattempt_set__user')
    
    # Add statistics for each quiz
    for quiz in quizzes:
        attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True)
        quiz.total_attempts = attempts.count()
        quiz.avg_score = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        quiz.success_rate = attempts.filter(score__gte=F('total_points') * 0.5).count()
        if quiz.total_attempts > 0:
            quiz.success_percentage = (quiz.success_rate / quiz.total_attempts) * 100
        else:
            quiz.success_percentage = 0
    
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
    questions_data = []
    
    for question in questions:
        question_data = {
            'id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'points': question.points,
            'explanation': question.explanation,
            'choices': []
        }
        
        if question.question_type == 'mcq':
            for choice in question.choices.all():
                question_data['choices'].append({
                    'id': choice.id,
                    'choice_text': choice.choice_text,
                    # 'is_correct': choice.is_correct  # Don't send this to frontend in production
                })
        
        questions_data.append(question_data)
    
    context = {
        'quiz': quiz,
        'questions': json.dumps(questions_data),  # Serialize for JavaScript
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
            # For now, give full points for open questions (can be manually graded later)
            answer.points_earned = question.points
            total_score += question.points
        
        elif question.question_type == 'true_false':
            user_answer = answer_data.get('true_false_answer')
            print(f"[v0] DEBUG True/False Question {question_id}:")
            print(f"[v0] User answer received: {user_answer} (type: {type(user_answer)})")
            
            if user_answer is not None:
                # Convert user answer to boolean
                if isinstance(user_answer, str):
                    user_bool = user_answer.lower().strip() in ['true', 'vrai', '1', 'oui', 'yes']
                else:
                    user_bool = bool(user_answer)
                
                answer.true_false_answer = user_bool
                print(f"[v0] User boolean answer: {user_bool}")
                
                # Find the correct answer
                correct_choice = question.choices.filter(is_correct=True).first()
                print(f"[v0] Correct choice found: {correct_choice}")
                
                if correct_choice:
                    correct_text = correct_choice.choice_text.lower().strip()
                    correct_bool = correct_text in ['true', 'vrai', '1', 'oui', 'yes']
                    print(f"[v0] Correct choice text: '{correct_text}' -> boolean: {correct_bool}")
                    
                    # Compare boolean values
                    if user_bool == correct_bool:
                        answer.is_correct = True
                        answer.points_earned = question.points
                        total_score += question.points
                        print(f"[v0] CORRECT! {user_bool} == {correct_bool}")
                    else:
                        answer.is_correct = False
                        answer.points_earned = 0
                        print(f"[v0] INCORRECT! {user_bool} != {correct_bool}")
                else:
                    answer.is_correct = False
                    answer.points_earned = 0
                    print(f"[v0] ERROR: No correct choice found for question")
            else:
                answer.is_correct = False
                answer.points_earned = 0
                print(f"[v0] No answer provided")
            
            print(f"[v0] Final result - is_correct: {answer.is_correct}, points: {answer.points_earned}")

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
    
    score_percentage = (attempt.score / attempt.total_points * 100) if attempt.total_points > 0 else 0
    excellent_threshold = 80
    good_threshold = 60
    
    recommended_quizzes = Quiz.objects.filter(
        subject=attempt.quiz.subject,
        is_published=True
    ).exclude(
        id=attempt.quiz.id
    ).prefetch_related('questions')[:6]  # Limit to 6 recommendations
    
    context = {
        'attempt': attempt,
        'answers': answers,
        'quiz': attempt.quiz,
        'score_percentage': score_percentage,
        'excellent_threshold': excellent_threshold,
        'good_threshold': good_threshold,
        'recommended_quizzes': recommended_quizzes,  # Added recommended quizzes
    }
    return render(request, 'quiz/results.html', context)

# Vues pour les enseignants
@login_required
def upload_pdf(request):
    """Téléversement de PDF par les enseignants"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    subjects_count = Subject.objects.count()
    print(f"[v0] Number of subjects in database: {subjects_count}")
    if subjects_count == 0:
        print(f"[v0] WARNING: No subjects found in database. Run create_subjects.py script first!")
    else:
        subjects_list = list(Subject.objects.values_list('name', flat=True))
        print(f"[v0] Available subjects: {subjects_list}")
    
    if request.method == 'POST':
        print(f"[v0] POST request received for PDF upload")
        form = CourseUploadForm(request.POST, request.FILES)
        print(f"[v0] Form data: {request.POST}")
        print(f"[v0] Files: {request.FILES}")
        
        print(f"[v0] Form fields: {list(form.fields.keys())}")
        if 'subject' in form.fields:
            subject_field = form.fields['subject']
            print(f"[v0] Subject field queryset count: {subject_field.queryset.count()}")
        
        if form.is_valid():
            print(f"[v0] Form is valid, saving course")
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            print(f"[v0] Course saved with ID: {course.id}")
            
            messages.success(request, "PDF téléversé avec succès! Vous pouvez maintenant créer des quiz basés sur ce cours.")
            print(f"[v0] Redirecting to create_quiz_from_course with course_id: {course.id}")
            return redirect('create_quiz_from_course', course_id=course.id)
        else:
            print(f"[v0] Form is not valid. Errors: {form.errors}")
            messages.error(request, "Erreur lors du téléversement. Veuillez vérifier les informations saisies.")
    else:
        form = CourseUploadForm()
        print(f"[v0] Form initialized. Subject field queryset: {form.fields['subject'].queryset.count()}")
    
    context = {
        'form': form,
        'subjects_count': subjects_count,
    }
    return render(request, 'teacher/upload_pdf.html', context)

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
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'update_quiz':
                # Update quiz basic info
                quiz.title = data.get('title', quiz.title)
                quiz.description = data.get('description', quiz.description)
                quiz.time_limit = data.get('time_limit', quiz.time_limit)
                quiz.save()
                
                return JsonResponse({'success': True, 'message': 'Quiz mis à jour avec succès'})
                
            elif action == 'save_questions':
                # Save questions (existing functionality)
                return save_quiz_questions(request, quiz_id)
                
            elif action == 'publish':
                # Publish quiz (existing functionality)
                return publish_quiz(request, quiz_id)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
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

@login_required
@require_http_methods(["GET"])
def get_quiz_questions(request, quiz_id):
    """Récupérer les questions existantes d'un quiz"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    questions = quiz.questions.prefetch_related('choices').all()
    
    questions_data = []
    for question in questions:
        question_data = {
            'question_text': question.question_text,
            'question_type': question.question_type,
            'points': question.points,
            'explanation': question.explanation,
            'difficulty': 'medium',  # Default value since not in model
        }
        
        if question.question_type == 'mcq':
            question_data['choices'] = [
                {
                    'text': choice.choice_text,
                    'is_correct': choice.is_correct
                }
                for choice in question.choices.all()
            ]
        
        questions_data.append(question_data)
    
    return JsonResponse({
        'success': True,
        'questions': questions_data
    })

@login_required
def quiz_participants(request, quiz_id):
    """Voir les participants d'un quiz spécifique et leurs scores"""
    if request.user.user_type != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('home')
    
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    
    attempts = QuizAttempt.objects.filter(
        quiz=quiz, 
        is_completed=True
    ).select_related('user').order_by('-completed_at')
    
    # Calculate statistics
    total_attempts = attempts.count()
    if total_attempts > 0:
        avg_score = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        success_count = attempts.filter(score__gte=F('total_points') * 0.5).count()
        success_rate = (success_count / total_attempts) * 100
    else:
        avg_score = 0
        success_rate = 0
        success_count = 0
    
    # Add percentage and status to each attempt
    for attempt in attempts:
        if attempt.total_points > 0:
            attempt.percentage = (attempt.score / attempt.total_points) * 100
            attempt.is_passing = attempt.percentage >= 50
        else:
            attempt.percentage = 0
            attempt.is_passing = False
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'success_rate': round(success_rate, 1),
        'success_count': success_count,
    }
    return render(request, 'teacher/quiz_participants.html', context)
