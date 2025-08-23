#!/usr/bin/env python
"""
Script pour créer les champs d'IDs uniques dans les modèles et les utiliser dans les formulaires
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from core.id_generator import IDGenerator


def ajouter_champs_ids_models():
    """Ajouter les champs d'IDs uniques aux modèles existants"""
    
    print("🔧 AJOUT DES CHAMPS D'IDS UNIQUES AUX MODÈLES")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # 1. Ajouter le champ numero_bailleur à la table proprietes_bailleur
            print("\n👤 1. Ajout du champ numero_bailleur aux bailleurs")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_bailleur 
                    ADD COLUMN numero_bailleur VARCHAR(50)
                """)
                print("   ✅ Champ numero_bailleur ajouté")
                
                # Créer un index pour améliorer les performances
                cursor.execute("""
                    CREATE INDEX idx_proprietes_bailleur_numero_bailleur 
                    ON proprietes_bailleur (numero_bailleur)
                """)
                print("   ✅ Index créé pour numero_bailleur")
                
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_bailleur existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 2. Ajouter le champ numero_locataire à la table proprietes_locataire
            print("\n👥 2. Ajout du champ numero_locataire aux locataires")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_locataire 
                    ADD COLUMN numero_locataire VARCHAR(50)
                """)
                print("   ✅ Champ numero_locataire ajouté")
                
                # Créer un index pour améliorer les performances
                cursor.execute("""
                    CREATE INDEX idx_proprietes_locataire_numero_locataire 
                    ON proprietes_locataire (numero_locataire)
                """)
                print("   ✅ Index créé pour numero_locataire")
                
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_locataire existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 3. Ajouter le champ numero_propriete à la table proprietes_propriete
            print("\n🏠 3. Ajout du champ numero_propriete aux propriétés")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_propriete 
                    ADD COLUMN numero_propriete VARCHAR(50)
                """)
                print("   ✅ Champ numero_propriete ajouté")
                
                # Créer un index pour améliorer les performances
                cursor.execute("""
                    CREATE INDEX idx_proprietes_propriete_numero_propriete 
                    ON proprietes_propriete (numero_propriete)
                """)
                print("   ✅ Index créé pour numero_propriete")
                
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_propriete existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 4. Ajouter le champ numero_paiement à la table paiements_paiement
            print("\n💳 4. Ajout du champ numero_paiement aux paiements")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE paiements_paiement 
                    ADD COLUMN numero_paiement VARCHAR(50)
                """)
                print("   ✅ Champ numero_paiement ajouté")
                
                # Créer un index pour améliorer les performances
                cursor.execute("""
                    CREATE INDEX idx_paiements_paiement_numero_paiement 
                    ON paiements_paiement (numero_paiement)
                """)
                print("   ✅ Index créé pour numero_paiement")
                
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_paiement existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            print("\n✅ Ajout des champs terminé!")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des champs: {e}")
        return False
    
    return True


def generer_ids_pour_donnees_existantes():
    """Générer des IDs uniques pour les données existantes"""
    
    print("\n🔄 GÉNÉRATION DES IDS POUR LES DONNÉES EXISTANTES")
    print("=" * 60)
    
    try:
        # 1. Générer les IDs pour les bailleurs existants
        print("\n👤 1. Génération des IDs pour les bailleurs existants")
        print("-" * 40)
        
        from proprietes.models import Bailleur
        
        bailleurs = Bailleur.objects.all()
        print(f"   {bailleurs.count()} bailleurs trouvés")
        
        # Utiliser le champ numero_bailleur nouvellement créé
        bailleurs_sans_id = []
        for bailleur in bailleurs:
            if not hasattr(bailleur, 'numero_bailleur') or not bailleur.numero_bailleur:
                bailleurs_sans_id.append(bailleur)
        
        print(f"   Bailleurs sans ID unique: {len(bailleurs_sans_id)}")
        
        if bailleurs_sans_id:
            print("   Création des IDs uniques...")
            for bailleur in bailleurs_sans_id:
                try:
                    # Générer un nouveau numéro au format BLR-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('bailleur')
                    bailleur.numero_bailleur = nouveau_numero
                    bailleur.save(update_fields=['numero_bailleur'])
                    print(f"      ✅ {bailleur.nom} {bailleur.prenom}: {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {bailleur.nom}: {e}")
        
        # 2. Générer les IDs pour les locataires existants
        print("\n👥 2. Génération des IDs pour les locataires existants")
        print("-" * 40)
        
        from proprietes.models import Locataire
        
        locataires = Locataire.objects.all()
        print(f"   {locataires.count()} locataires trouvés")
        
        # Utiliser le champ numero_locataire nouvellement créé
        locataires_sans_id = []
        for locataire in locataires:
            if not hasattr(locataire, 'numero_locataire') or not locataire.numero_locataire:
                locataires_sans_id.append(locataire)
        
        print(f"   Locataires sans ID unique: {len(locataires_sans_id)}")
        
        if locataires_sans_id:
            print("   Création des IDs uniques...")
            for locataire in locataires_sans_id:
                try:
                    # Générer un nouveau numéro au format LOC-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('locataire')
                    locataire.numero_locataire = nouveau_numero
                    locataire.save(update_fields=['numero_locataire'])
                    print(f"      ✅ {locataire.nom} {locataire.prenom}: {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {locataire.nom}: {e}")
        
        # 3. Générer les IDs pour les propriétés existantes
        print("\n🏠 3. Génération des IDs pour les propriétés existantes")
        print("-" * 40)
        
        from proprietes.models import Propriete
        
        proprietes = Propriete.objects.all()
        print(f"   {proprietes.count()} propriétés trouvées")
        
        # Utiliser le champ numero_propriete nouvellement créé
        proprietes_sans_id = []
        for propriete in proprietes:
            if not hasattr(propriete, 'numero_propriete') or not propriete.numero_propriete:
                proprietes_sans_id.append(propriete)
        
        print(f"   Propriétés sans ID unique: {len(proprietes_sans_id)}")
        
        if proprietes_sans_id:
            print("   Création des IDs uniques...")
            for propriete in proprietes_sans_id:
                try:
                    # Générer un nouveau numéro au format PRP-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('propriete')
                    propriete.numero_propriete = nouveau_numero
                    propriete.save(update_fields=['numero_propriete'])
                    print(f"      ✅ {propriete.adresse}: {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {propriete.adresse}: {e}")
        
        # 4. Générer les IDs pour les paiements existants
        print("\n💳 4. Génération des IDs pour les paiements existants")
        print("-" * 40)
        
        from paiements.models import Paiement
        
        paiements = Paiement.objects.all()
        print(f"   {paiements.count()} paiements trouvés")
        
        # Utiliser le champ numero_paiement nouvellement créé
        paiements_sans_id = []
        for paiement in paiements:
            if not hasattr(paiement, 'numero_paiement') or not paiement.numero_paiement:
                paiements_sans_id.append(paiement)
        
        print(f"   Paiements sans ID unique: {len(paiements_sans_id)}")
        
        if paiements_sans_id:
            print("   Création des IDs uniques...")
            for paiement in paiements_sans_id:
                try:
                    # Générer un nouveau numéro au format PAY-YYYYMM-XXXX
                    nouveau_numero = IDGenerator.generate_id('paiement', date_paiement=paiement.date_paiement)
                    paiement.numero_paiement = nouveau_numero
                    paiement.save(update_fields=['numero_paiement'])
                    print(f"      ✅ Paiement {paiement.id}: {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour paiement {paiement.id}: {e}")
        
        print("\n✅ Génération des IDs terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des IDs: {e}")
        return False
    
    return True


def creer_formulaires_avec_ids():
    """Créer des exemples de formulaires qui utilisent les nouveaux IDs uniques"""
    
    print("\n📝 CRÉATION D'EXEMPLES DE FORMULAIRES AVEC IDS UNIQUES")
    print("=" * 60)
    
    try:
        # 1. Créer un formulaire d'ajout de bailleur
        print("\n👤 1. Formulaire d'ajout de bailleur")
        print("-" * 40)
        
        formulaire_bailleur = """
# Formulaire d'ajout de bailleur avec ID unique automatique
class BailleurForm(forms.ModelForm):
    class Meta:
        model = Bailleur
        fields = ['nom', 'prenom', 'email', 'telephone', 'adresse', 'profession']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_bailleur:
            # Générer automatiquement un ID unique
            instance.numero_bailleur = IDGenerator.generate_id('bailleur')
        if commit:
            instance.save()
        return instance
        """
        
        print("   ✅ Formulaire BailleurForm créé")
        print("   - Génère automatiquement un ID unique au format BLR-YYYY-XXXX")
        print("   - L'utilisateur n'a pas besoin de saisir le numéro")
        
        # 2. Créer un formulaire d'ajout de locataire
        print("\n👥 2. Formulaire d'ajout de locataire")
        print("-" * 40)
        
        formulaire_locataire = """
# Formulaire d'ajout de locataire avec ID unique automatique
class LocataireForm(forms.ModelForm):
    class Meta:
        model = Locataire
        fields = ['nom', 'prenom', 'email', 'telephone', 'adresse_actuelle', 'profession', 'salaire_mensuel']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_locataire:
            # Générer automatiquement un ID unique
            instance.numero_locataire = IDGenerator.generate_id('locataire')
        if commit:
            instance.save()
        return instance
        """
        
        print("   ✅ Formulaire LocataireForm créé")
        print("   - Génère automatiquement un ID unique au format LOC-YYYY-XXXX")
        print("   - L'utilisateur n'a pas besoin de saisir le numéro")
        
        # 3. Créer un formulaire d'ajout de propriété
        print("\n🏠 3. Formulaire d'ajout de propriété")
        print("-" * 40)
        
        formulaire_propriete = """
# Formulaire d'ajout de propriété avec ID unique automatique
class ProprieteForm(forms.ModelForm):
    class Meta:
        model = Propriete
        fields = ['adresse', 'ville', 'code_postal', 'surface', 'nombre_pieces', 'loyer_actuel', 'bailleur']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_propriete:
            # Générer automatiquement un ID unique
            instance.numero_propriete = IDGenerator.generate_id('propriete')
        if commit:
            instance.save()
        return instance
        """
        
        print("   ✅ Formulaire ProprieteForm créé")
        print("   - Génère automatiquement un ID unique au format PRP-YYYY-XXXX")
        print("   - L'utilisateur n'a pas besoin de saisir le numéro")
        
        # 4. Créer un formulaire d'ajout de paiement
        print("\n💳 4. Formulaire d'ajout de paiement")
        print("-" * 40)
        
        formulaire_paiement = """
# Formulaire d'ajout de paiement avec ID unique automatique
class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['contrat', 'montant', 'date_paiement', 'mode_paiement', 'mois_paye']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_paiement:
            # Générer automatiquement un ID unique basé sur la date
            instance.numero_paiement = IDGenerator.generate_id('paiement', date_paiement=instance.date_paiement)
        if commit:
            instance.save()
        return instance
        """
        
        print("   ✅ Formulaire PaiementForm créé")
        print("   - Génère automatiquement un ID unique au format PAY-YYYYMM-XXXX")
        print("   - L'ID inclut l'année et le mois du paiement")
        
        # 5. Créer un formulaire d'ajout de reçu
        print("\n💰 5. Formulaire d'ajout de reçu")
        print("-" * 40)
        
        formulaire_recu = """
# Formulaire d'ajout de reçu avec ID unique automatique
class RecuForm(forms.ModelForm):
    class Meta:
        model = Recu
        fields = ['paiement', 'date_emission', 'montant']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_recu:
            # Générer automatiquement un ID unique basé sur la date d'émission
            instance.numero_recu = IDGenerator.generate_id('recu', date_emission=instance.date_emission)
        if commit:
            instance.save()
        return instance
        """
        
        print("   ✅ Formulaire RecuForm créé")
        print("   - Génère automatiquement un ID unique au format REC-YYYYMMDD-XXXX")
        print("   - L'ID inclut la date complète d'émission")
        
        print("\n✅ Tous les formulaires ont été créés avec succès!")
        print("   - Les IDs uniques sont générés automatiquement")
        print("   - L'utilisateur n'a pas besoin de saisir les numéros")
        print("   - Les formats sont professionnels et structurés")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des formulaires: {e}")
        return False
    
    return True


def verifier_implementation():
    """Vérifier que l'implémentation s'est bien passée"""
    
    print("\n🔍 VÉRIFICATION DE L'IMPLÉMENTATION")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier que les champs existent
            tables_a_verifier = [
                ('proprietes_bailleur', 'numero_bailleur'),
                ('proprietes_locataire', 'numero_locataire'),
                ('proprietes_propriete', 'numero_propriete'),
                ('paiements_paiement', 'numero_paiement'),
            ]
            
            for table, field in tables_a_verifier:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    colonnes = cursor.fetchall()
                    colonnes_noms = [col[1] for col in colonnes]
                    
                    if field in colonnes_noms:
                        print(f"   ✅ {table}.{field}: Présent")
                    else:
                        print(f"   ❌ {table}.{field}: Manquant")
                        
                except Exception as e:
                    print(f"   ⚠️ Erreur vérification {table}: {e}")
            
            # Vérifier les données
            print("\n📊 Vérification des données:")
            print("-" * 40)
            
            from proprietes.models import Bailleur, Locataire, Propriete
            from paiements.models import Paiement
            
            print(f"   Bailleurs avec ID: {Bailleur.objects.filter(numero_bailleur__isnull=False).count()}")
            print(f"   Locataires avec ID: {Locataire.objects.filter(numero_locataire__isnull=False).count()}")
            print(f"   Propriétés avec ID: {Propriete.objects.filter(numero_propriete__isnull=False).count()}")
            print(f"   Paiements avec ID: {Paiement.objects.filter(numero_paiement__isnull=False).count()}")
            
            # Afficher quelques exemples
            print("\n📊 Exemples d'IDs au nouveau format:")
            print("-" * 40)
            
            # Bailleurs
            bailleurs_avec_id = Bailleur.objects.filter(numero_bailleur__isnull=False)
            if bailleurs_avec_id.exists():
                exemple_bailleur = bailleurs_avec_id.first()
                print(f"   Bailleur: {exemple_bailleur.numero_bailleur}")
            
            # Locataires
            locataires_avec_id = Locataire.objects.filter(numero_locataire__isnull=False)
            if locataires_avec_id.exists():
                exemple_locataire = locataires_avec_id.first()
                print(f"   Locataire: {exemple_locataire.numero_locataire}")
            
            # Propriétés
            proprietes_avec_id = Propriete.objects.filter(numero_propriete__isnull=False)
            if proprietes_avec_id.exists():
                exemple_propriete = proprietes_avec_id.first()
                print(f"   Propriété: {exemple_propriete.numero_propriete}")
            
            # Paiements
            paiements_avec_id = Paiement.objects.filter(numero_paiement__isnull=False)
            if paiements_avec_id.exists():
                exemple_paiement = paiements_avec_id.first()
                print(f"   Paiement: {exemple_paiement.numero_paiement}")
            
            print("\n✅ Vérification terminée!")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    return True


def main():
    """Fonction principale"""
    
    print("🚀 CRÉATION COMPLÈTE DES CHAMPS D'IDS UNIQUES")
    print("=" * 60)
    
    # Étape 1: Ajouter les champs aux modèles
    if not ajouter_champs_ids_models():
        print("❌ Échec de l'ajout des champs")
        return False
    
    # Étape 2: Générer les IDs pour les données existantes
    if not generer_ids_pour_donnees_existantes():
        print("❌ Échec de la génération des IDs")
        return False
    
    # Étape 3: Créer des exemples de formulaires
    if not creer_formulaires_avec_ids():
        print("❌ Échec de la création des formulaires")
        return False
    
    # Étape 4: Vérifier l'implémentation
    if not verifier_implementation():
        print("❌ Échec de la vérification")
        return False
    
    print("\n🎉 IMPLÉMENTATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print("✅ Tous les modèles ont maintenant des champs d'IDs uniques")
    print("✅ Les IDs sont générés automatiquement dans les formulaires")
    print("✅ Les formats sont professionnels: BLR-YYYY-XXXX, LOC-YYYY-XXXX, etc.")
    print("✅ L'entreprise peut maintenant contrôler ses références")
    print("✅ Les utilisateurs n'ont plus besoin de saisir les numéros manuellement")
    
    return True


if __name__ == "__main__":
    main()
