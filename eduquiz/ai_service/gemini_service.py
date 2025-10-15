import google.generativeai as genai
from django.conf import settings
import PyPDF2
import json
import io
from typing import Dict, List, Any

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extraire le texte d'un fichier PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF: {e}")
            return ""
    
    def analyze_pdf_and_suggest_quiz(self, pdf_content: str, subject: str, level: str, num_questions: int = 15) -> Dict[str, Any]:
        """Analyser le contenu PDF et suggérer des questions de quiz"""
        
        prompt = f"""
        Tu es un expert pédagogique spécialisé en {subject} pour le niveau {level}.
        
        Analyse le contenu suivant d'un cours et génère {num_questions} questions de quiz variées et pertinentes.
        
        CONTENU DU COURS:
        {pdf_content[:8000]}  # Limiter à 8000 caractères pour éviter les limites de tokens
        
        INSTRUCTIONS:
        1. Crée des questions de SEULEMENT types : QCM (4 choix)
        2. PAS de questions Vrai/Faux - elles sont interdites
        3. Varie les niveaux de difficulté : facile, moyen, difficile
        4. Assure-toi que les questions couvrent les concepts clés du cours
        5. Pour les QCM, une seule réponse doit être correcte
        6. Ajoute des explications détaillées pour chaque réponse
        7. Les points sont calculés automatiquement selon la difficulté
        
        RÉPONSE ATTENDUE (format JSON strict):
        {{
            "quiz_title": "Titre suggéré pour le quiz",
            "quiz_description": "Description du quiz",
            "estimated_time": 15,
            "questions": [
                {{
                    "question_text": "Texte de la question",
                    "question_type": "mcq|open",
                    "difficulty": "easy|medium|hard",
                    "points": 5,
                    "choices": [
                        {{"text": "Choix A", "is_correct": false}},
                        {{"text": "Choix B", "is_correct": true}},
                        {{"text": "Choix C", "is_correct": false}},
                        {{"text": "Choix D", "is_correct": false}}
                    ],
                    "explanation": "Explication détaillée de la réponse correcte"
                }}
            ]
        }}
        
        IMPORTANT: Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Nettoyer la réponse pour extraire le JSON
            response_text = response.text.strip()
            
            # Supprimer les balises markdown si présentes
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parser le JSON
            quiz_data = json.loads(response_text)
            
            return {
                'success': True,
                'data': quiz_data
            }
            
        except json.JSONDecodeError as e:
            print(f"Erreur de parsing JSON: {e}")
            print(f"Réponse brute: {response.text}")
            return {
                'success': False,
                'error': 'Erreur de format de réponse de l\'IA'
            }
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def evaluate_true_false_answer(self, question_text: str, user_answer: bool, context: str = "") -> Dict[str, Any]:
        """Évaluer une réponse vrai/faux avec l'IA Gemini"""
        
        prompt = f"""
        Tu es un expert pédagogique. Évalue si cette réponse à une question vrai/faux est correcte.
        
        QUESTION: {question_text}
        RÉPONSE DE L'ÉLÈVE: {"Vrai" if user_answer else "Faux"}
        CONTEXTE SUPPLÉMENTAIRE: {context}
        
        Analyse la question et détermine si la réponse de l'élève est correcte.
        
        Réponds UNIQUEMENT avec ce format JSON:
        {{
            "is_correct": true/false,
            "explanation": "Explication détaillée de pourquoi la réponse est correcte ou incorrecte"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            
            result = json.loads(response_text)
            
            return {
                'success': True,
                'is_correct': result.get('is_correct', False),
                'explanation': result.get('explanation', '')
            }
            
        except Exception as e:
            print(f"Erreur évaluation IA: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_quiz_points(self, difficulty: str, time_limit: int, subject: str) -> int:
        """Suggérer le nombre de points pour un quiz basé sur la difficulté et le temps"""
        
        prompt = f"""
        Tu es un expert en évaluation pédagogique.
        
        Suggère le nombre total de points approprié pour un quiz avec ces caractéristiques:
        - Matière: {subject}
        - Difficulté: {difficulty}
        - Temps limite: {time_limit} minutes
        
        Considère que:
        - Un quiz facile devrait donner moins de points
        - Un quiz difficile devrait donner plus de points
        - Plus de temps permet des questions plus complexes
        - Les points doivent motiver les élèves
        
        Réponds UNIQUEMENT avec un nombre entier entre 20 et 200.
        """
        
        try:
            response = self.model.generate_content(prompt)
            points = int(response.text.strip())
            
            # Validation des limites
            if points < 20:
                points = 20
            elif points > 200:
                points = 200
                
            return points
            
        except Exception as e:
            print(f"Erreur suggestion points: {e}")
            # Fallback calculation
            difficulty_multiplier = {'easy': 1, 'medium': 1.5, 'hard': 2}
            base_points = max(20, time_limit)
            return int(base_points * difficulty_multiplier.get(difficulty, 1))

    def improve_question(self, question_text: str, subject: str, level: str) -> Dict[str, Any]:
        """Améliorer une question existante"""
        
        prompt = f"""
        Tu es un expert pédagogique en {subject} pour le niveau {level}.
        
        Améliore cette question de quiz en la rendant plus claire, plus précise et plus adaptée au niveau:
        
        QUESTION ACTUELLE: {question_text}
        
        Propose 3 versions améliorées avec des explications sur les améliorations apportées.
        
        Format JSON:
        {{
            "improved_questions": [
                {{
                    "question": "Version améliorée 1",
                    "improvements": "Explication des améliorations"
                }},
                {{
                    "question": "Version améliorée 2", 
                    "improvements": "Explication des améliorations"
                }},
                {{
                    "question": "Version améliorée 3",
                    "improvements": "Explication des améliorations"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            
            return {
                'success': True,
                'data': json.loads(response_text)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
