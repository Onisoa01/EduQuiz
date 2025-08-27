import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduquiz.settings')
django.setup()

from quiz.models import Subject
from django.utils.text import slugify

def create_subjects():
    """Créer les matières de base pour le Lycée Saint Famille"""
    
    subjects_data = [
        # Matières principales
        {'name': 'Mathématiques', 'icon': 'fas fa-calculator', 'color': 'blue'},
        {'name': 'Français', 'icon': 'fas fa-book-open', 'color': 'red'},
        {'name': 'Anglais', 'icon': 'fas fa-globe', 'color': 'green'},
        {'name': 'Histoire-Géographie', 'icon': 'fas fa-map', 'color': 'orange'},
        {'name': 'Sciences Physiques', 'icon': 'fas fa-atom', 'color': 'purple'},
        {'name': 'Sciences de la Vie et de la Terre', 'icon': 'fas fa-leaf', 'color': 'green'},
        {'name': 'Philosophie', 'icon': 'fas fa-brain', 'color': 'indigo'},
        {'name': 'Économie', 'icon': 'fas fa-chart-line', 'color': 'yellow'},
        
        # Matières techniques
        {'name': 'Informatique', 'icon': 'fas fa-laptop-code', 'color': 'cyan'},
        {'name': 'Arts Plastiques', 'icon': 'fas fa-palette', 'color': 'pink'},
        {'name': 'Éducation Physique', 'icon': 'fas fa-running', 'color': 'teal'},
        {'name': 'Musique', 'icon': 'fas fa-music', 'color': 'violet'},
        
        # Langues
        {'name': 'Espagnol', 'icon': 'fas fa-language', 'color': 'red'},
        {'name': 'Allemand', 'icon': 'fas fa-language', 'color': 'gray'},
        {'name': 'Italien', 'icon': 'fas fa-language', 'color': 'green'},
    ]
    
    created_count = 0
    updated_count = 0
    
    for subject_data in subjects_data:
        slug = slugify(subject_data['name'])
        subject, created = Subject.objects.get_or_create(
            slug=slug,
            defaults={
                'name': subject_data['name'],
                'icon': subject_data['icon'],
                'color': subject_data['color']
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Matière créée: {subject.name}")
        else:
            # Mettre à jour si nécessaire
            subject.icon = subject_data['icon']
            subject.color = subject_data['color']
            subject.save()
            updated_count += 1
            print(f"→ Matière mise à jour: {subject.name}")
    
    print(f"\n📚 Résumé:")
    print(f"   - {created_count} matières créées")
    print(f"   - {updated_count} matières mises à jour")
    print(f"   - {Subject.objects.count()} matières au total")

if __name__ == '__main__':
    print("🏫 Création des matières pour le Lycée Saint Famille...")
    create_subjects()
    print("✅ Terminé!")
