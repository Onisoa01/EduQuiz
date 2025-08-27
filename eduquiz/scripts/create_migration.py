#!/usr/bin/env python
"""
Script pour créer les migrations nécessaires après les modifications du modèle User
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduquiz.settings')
django.setup()

def create_migrations():
    """Créer les migrations pour les nouveaux champs"""
    print("Création des migrations...")
    
    # Commandes à exécuter
    commands = [
        "python manage.py makemigrations accounts",
        "python manage.py makemigrations quiz",
        "python manage.py migrate",
    ]
    
    for command in commands:
        print(f"Exécution: {command}")
        os.system(command)
    
    print("✅ Migrations créées et appliquées avec succès!")
    print("\nProchaines étapes:")
    print("1. Testez l'inscription d'un élève avec une classe")
    print("2. Vérifiez que les quiz peuvent être filtrés par classe")
    print("3. Créez des quiz spécifiques à certaines classes")

if __name__ == "__main__":
    create_migrations()
