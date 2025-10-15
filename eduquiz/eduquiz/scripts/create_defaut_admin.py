import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduquiz.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_default_admin():
    """
    Crée un compte administrateur par défaut
    Username: admin
    Password: admin123
    """
    
    # Vérifier si l'admin existe déjà
    if User.objects.filter(username='admin').exists():
        print("✓ Le compte admin existe déjà")
        admin_user = User.objects.get(username='admin')
        print(f"  Username: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Type: {admin_user.get_user_type_display()}")
        return
    
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@saintfamille.edu',
        password='admin123',
        first_name='Administrateur',
        last_name='Système',
        user_type='admin'
    )
    
    print("✓ Compte administrateur créé avec succès!")
    print(f"  Username: admin")
    print(f"  Password: admin123")
    print(f"  Email: admin@saintfamille.edu")
    print(f"  Type: {admin_user.get_user_type_display()}")
    print("\n⚠️  N'oubliez pas de changer le mot de passe après la première connexion!")

if __name__ == '__main__':
    create_default_admin()
