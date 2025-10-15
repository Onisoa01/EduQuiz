import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduquiz.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import AdminProfile

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
        return
    
    # Créer l'utilisateur admin
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@saintfamille.edu',
        password='admin123',
        first_name='Administrateur',
        last_name='Système',
        user_type='admin'
    )
    
    # Créer le profil admin
    AdminProfile.objects.create(
        user=admin_user,
        department='Administration'
    )
    
    print("✓ Compte administrateur créé avec succès!")
    print(f"  Username: admin")
    print(f"  Password: admin123")
    print(f"  Email: admin@saintfamille.edu")
    print("\n⚠️  N'oubliez pas de changer le mot de passe après la première connexion!")

if __name__ == '__main__':
    create_default_admin()
