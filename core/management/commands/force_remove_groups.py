"""
Commande pour forcer la suppression des groupes inutiles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

class Command(BaseCommand):
    help = 'Force la suppression des groupes inutiles'

    def handle(self, *args, **options):
        # Groupes à supprimer définitivement
        groupes_a_supprimer = ['COMPTABILITE', 'TEST', 'TEST_GROUP', 'TEST_GROUP_PHONE']
        
        with transaction.atomic():
            for nom_groupe in groupes_a_supprimer:
                try:
                    # Supprimer le groupe Django
                    groupe_django = Group.objects.filter(name=nom_groupe)
                    if groupe_django.exists():
                        groupe_django.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f"Groupe Django '{nom_groupe}' supprimé")
                        )
                    
                    # Supprimer le groupe de travail personnalisé
                    from utilisateurs.models import GroupeTravail
                    groupe_travail = GroupeTravail.objects.filter(nom=nom_groupe)
                    if groupe_travail.exists():
                        groupe_travail.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f"GroupeTravail '{nom_groupe}' supprimé")
                        )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Erreur lors de la suppression de '{nom_groupe}': {e}")
                    )
        
        # Vérifier les groupes restants
        from utilisateurs.models import GroupeTravail
        groupes_restants = GroupeTravail.objects.all()
        self.stdout.write(
            self.style.SUCCESS(f"Groupes restants: {list(groupes_restants.values_list('nom', flat=True))}")
        )
