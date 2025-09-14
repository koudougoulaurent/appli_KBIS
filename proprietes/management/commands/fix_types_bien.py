from django.core.management.base import BaseCommand
from proprietes.models import TypeBien

class Command(BaseCommand):
    help = 'Ajoute les types de biens de base s\'ils n\'existent pas'

    def handle(self, *args, **options):
        """Exécute la commande pour ajouter les types de biens."""
        self.stdout.write("🏠 Vérification et création des types de biens...")
        
        types_data = [
            {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
            {'nom': 'Maison', 'description': 'Maison individuelle'},
            {'nom': 'Studio', 'description': 'Studio meublé'},
            {'nom': 'Loft', 'description': 'Loft industriel'},
            {'nom': 'Villa', 'description': 'Villa avec jardin'},
            {'nom': 'Duplex', 'description': 'Duplex sur deux niveaux'},
            {'nom': 'Penthouse', 'description': 'Penthouse de luxe'},
            {'nom': 'Château', 'description': 'Château ou manoir'},
            {'nom': 'Ferme', 'description': 'Ferme ou propriété rurale'},
            {'nom': 'Bureau', 'description': 'Local commercial ou bureau'},
            {'nom': 'Commerce', 'description': 'Local commercial'},
            {'nom': 'Entrepôt', 'description': 'Entrepôt ou local industriel'},
            {'nom': 'Garage', 'description': 'Garage ou parking'},
            {'nom': 'Terrain', 'description': 'Terrain constructible'},
            {'nom': 'Autre', 'description': 'Autre type de bien'},
        ]
        
        types_crees = []
        types_existants = []
        
        for type_data in types_data:
            type_bien, created = TypeBien.objects.get_or_create(
                nom=type_data['nom'],
                defaults=type_data
            )
            if created:
                types_crees.append(type_bien)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Type créé: {type_bien.nom}")
                )
            else:
                types_existants.append(type_bien)
                self.stdout.write(f"ℹ️  Type existant: {type_bien.nom}")
        
        self.stdout.write(f"\n📊 Résumé:")
        self.stdout.write(f"   - Types créés: {len(types_crees)}")
        self.stdout.write(f"   - Types existants: {len(types_existants)}")
        self.stdout.write(f"   - Total dans la base: {TypeBien.objects.count()}")
        
        if types_crees:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 SUCCÈS ! {len(types_crees)} nouveaux types de biens ajoutés.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Tous les types de biens étaient déjà présents.")
            )
        
        self.stdout.write(f"\n📋 Liste des types de biens disponibles:")
        for type_bien in TypeBien.objects.all():
            self.stdout.write(f"   - {type_bien.nom}: {type_bien.description}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🌐 Votre formulaire d'ajout de propriétés devrait maintenant fonctionner correctement !")
        )
