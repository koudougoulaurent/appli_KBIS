"""
Commande pour nettoyer les groupes de travail et ne garder que les 4 essentiels
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

class Command(BaseCommand):
    help = 'Nettoie les groupes de travail pour ne garder que les 4 essentiels'

    def handle(self, *args, **options):
        # Groupes à conserver
        groupes_essentiels = ['PRIVILEGE', 'CAISSE', 'ADMINISTRATION', 'CONTROLES']
        
        # Groupes à supprimer
        groupes_a_supprimer = ['COMPTABILITE', 'TEST', 'TEST_GROUP', 'TEST_GROUP_PHONE']
        
        with transaction.atomic():
            # Supprimer les groupes inutiles
            for nom_groupe in groupes_a_supprimer:
                try:
                    groupe = Group.objects.get(name=nom_groupe)
                    # Vérifier s'il y a des utilisateurs dans ce groupe
                    utilisateurs_count = groupe.user_set.count()
                    if utilisateurs_count > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Le groupe '{nom_groupe}' a {utilisateurs_count} utilisateur(s). "
                                f"Les utilisateurs seront déplacés vers le groupe 'CAISSE'."
                            )
                        )
                        # Déplacer les utilisateurs vers le groupe CAISSE
                        groupe_caisse = Group.objects.get(name='CAISSE')
                        for user in groupe.user_set.all():
                            user.groups.add(groupe_caisse)
                            user.groups.remove(groupe)
                    
                    groupe.delete()
                    self.stdout.write(
                        self.style.SUCCESS(f"Groupe '{nom_groupe}' supprimé avec succès")
                    )
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Le groupe '{nom_groupe}' n'existe pas")
                    )
            
            # Vérifier que les groupes essentiels existent
            for nom_groupe in groupes_essentiels:
                groupe, created = Group.objects.get_or_create(name=nom_groupe)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Groupe '{nom_groupe}' créé")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"Groupe '{nom_groupe}' existe déjà")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                "Nettoyage terminé ! Seuls les 4 groupes essentiels sont conservés : "
                "PRIVILEGE, CAISSE, ADMINISTRATION, CONTROLES"
            )
        )
