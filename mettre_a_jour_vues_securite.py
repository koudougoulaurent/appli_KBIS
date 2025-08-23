#!/usr/bin/env python
"""
Script pour mettre à jour les vues avec la sécurité et la sauvegarde des données
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien
from proprietes.forms import BailleurForm, LocataireForm, ProprieteForm
from core.save_handlers import DataSaveHandler
from core.validators import SecurityValidator, DataSanitizer


def update_proprietes_views():
    """Mettre à jour les vues des propriétés avec la sécurité"""
    
    print("🔄 Mise à jour des vues des propriétés avec la sécurité")
    print("=" * 60)
    
    # Mettre à jour la vue ajouter_bailleur
    update_ajouter_bailleur_view()
    
    # Mettre à jour la vue modifier_bailleur
    update_modifier_bailleur_view()
    
    # Mettre à jour la vue ajouter_locataire
    update_ajouter_locataire_view()
    
    # Mettre à jour la vue modifier_locataire
    update_modifier_locataire_view()
    
    # Mettre à jour la vue ajouter_propriete
    update_ajouter_propriete_view()
    
    # Mettre à jour la vue modifier_propriete
    update_modifier_propriete_view()
    
    print("✅ Mise à jour des vues terminée")


def update_ajouter_bailleur_view():
    """Mettre à jour la vue ajouter_bailleur"""
    
    content = '''@login_required
def ajouter_bailleur(request):
    """
    Vue sécurisée pour ajouter un bailleur
    """
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = BailleurForm(request.POST)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['nom'] = DataSanitizer.sanitize_name(cleaned_data['nom'])
                cleaned_data['prenom'] = DataSanitizer.sanitize_name(cleaned_data['prenom'])
                cleaned_data['email'] = DataSanitizer.sanitize_email(cleaned_data['email'])
                cleaned_data['telephone'] = DataSanitizer.sanitize_phone(cleaned_data['telephone'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                if cleaned_data.get('iban'):
                    cleaned_data['iban'] = DataSanitizer.sanitize_iban(cleaned_data['iban'])
                
                # Sauvegarder avec le gestionnaire sécurisé
                bailleur, success, message = DataSaveHandler.save_bailleur(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Bailleur ajouté avec succès: {message}')
                    return redirect('proprietes:bailleurs_liste')
                else:
                    messages.error(request, f'Erreur lors de l\'ajout: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur ajouter_bailleur: {e}")
    else:
        form = BailleurForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un Bailleur',
        'submit_text': 'Enregistrer le Bailleur'
    }
    return render(request, 'proprietes/bailleur_ajouter.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef ajouter_bailleur\(request\):.*?return render\(request, \'proprietes/bailleur_ajouter\.html\'\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue ajouter_bailleur mise à jour")
    else:
        print("⚠️ Vue ajouter_bailleur non trouvée")


def update_modifier_bailleur_view():
    """Mettre à jour la vue modifier_bailleur"""
    
    content = '''@login_required
def modifier_bailleur(request, pk):
    """
    Vue sécurisée pour modifier un bailleur
    """
    bailleur = get_object_or_404(Bailleur, pk=pk)
    
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = BailleurForm(request.POST, instance=bailleur)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['nom'] = DataSanitizer.sanitize_name(cleaned_data['nom'])
                cleaned_data['prenom'] = DataSanitizer.sanitize_name(cleaned_data['prenom'])
                cleaned_data['email'] = DataSanitizer.sanitize_email(cleaned_data['email'])
                cleaned_data['telephone'] = DataSanitizer.sanitize_phone(cleaned_data['telephone'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                if cleaned_data.get('iban'):
                    cleaned_data['iban'] = DataSanitizer.sanitize_iban(cleaned_data['iban'])
                
                # Ajouter l'ID pour la mise à jour
                cleaned_data['id'] = pk
                
                # Sauvegarder avec le gestionnaire sécurisé
                bailleur, success, message = DataSaveHandler.save_bailleur(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Bailleur modifié avec succès: {message}')
                    return redirect('proprietes:detail_bailleur', pk=pk)
                else:
                    messages.error(request, f'Erreur lors de la modification: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur modifier_bailleur: {e}")
    else:
        form = BailleurForm(instance=bailleur)
    
    context = {
        'form': form,
        'bailleur': bailleur,
        'title': 'Modifier le Bailleur',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'proprietes/bailleur_modifier.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef modifier_bailleur\(request, pk\):.*?return render\(request, \'proprietes/bailleur_modifier\.html\', context\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue modifier_bailleur mise à jour")
    else:
        print("⚠️ Vue modifier_bailleur non trouvée")


def update_ajouter_locataire_view():
    """Mettre à jour la vue ajouter_locataire"""
    
    content = '''@login_required
def ajouter_locataire(request):
    """
    Vue sécurisée pour ajouter un locataire
    """
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = LocataireForm(request.POST)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['nom'] = DataSanitizer.sanitize_name(cleaned_data['nom'])
                cleaned_data['prenom'] = DataSanitizer.sanitize_name(cleaned_data['prenom'])
                cleaned_data['email'] = DataSanitizer.sanitize_email(cleaned_data['email'])
                cleaned_data['telephone'] = DataSanitizer.sanitize_phone(cleaned_data['telephone'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                # Sauvegarder avec le gestionnaire sécurisé
                locataire, success, message = DataSaveHandler.save_locataire(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Locataire ajouté avec succès: {message}')
                    return redirect('proprietes:locataires_liste')
                else:
                    messages.error(request, f'Erreur lors de l\'ajout: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur ajouter_locataire: {e}")
    else:
        form = LocataireForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un Locataire',
        'submit_text': 'Enregistrer le Locataire'
    }
    return render(request, 'proprietes/locataire_ajouter.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef ajouter_locataire\(request\):.*?return render\(request, \'proprietes/locataire_ajouter\.html\'\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue ajouter_locataire mise à jour")
    else:
        print("⚠️ Vue ajouter_locataire non trouvée")


def update_modifier_locataire_view():
    """Mettre à jour la vue modifier_locataire"""
    
    content = '''@login_required
def modifier_locataire(request, pk):
    """
    Vue sécurisée pour modifier un locataire
    """
    locataire = get_object_or_404(Locataire, pk=pk)
    
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = LocataireForm(request.POST, instance=locataire)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['nom'] = DataSanitizer.sanitize_name(cleaned_data['nom'])
                cleaned_data['prenom'] = DataSanitizer.sanitize_name(cleaned_data['prenom'])
                cleaned_data['email'] = DataSanitizer.sanitize_email(cleaned_data['email'])
                cleaned_data['telephone'] = DataSanitizer.sanitize_phone(cleaned_data['telephone'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                # Ajouter l'ID pour la mise à jour
                cleaned_data['id'] = pk
                
                # Sauvegarder avec le gestionnaire sécurisé
                locataire, success, message = DataSaveHandler.save_locataire(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Locataire modifié avec succès: {message}')
                    return redirect('proprietes:detail_locataire', pk=pk)
                else:
                    messages.error(request, f'Erreur lors de la modification: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur modifier_locataire: {e}")
    else:
        form = LocataireForm(instance=locataire)
    
    context = {
        'form': form,
        'locataire': locataire,
        'title': 'Modifier le Locataire',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'proprietes/locataire_modifier.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef modifier_locataire\(request, pk\):.*?return render\(request, \'proprietes/locataire_modifier\.html\', context\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue modifier_locataire mise à jour")
    else:
        print("⚠️ Vue modifier_locataire non trouvée")


def update_ajouter_propriete_view():
    """Mettre à jour la vue ajouter_propriete"""
    
    content = '''@login_required
def ajouter_propriete(request):
    """
    Vue sécurisée pour ajouter une propriété
    """
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = ProprieteForm(request.POST)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['titre'] = DataSanitizer.sanitize_text(cleaned_data['titre'])
                cleaned_data['ville'] = DataSanitizer.sanitize_name(cleaned_data['ville'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                # Valider les montants
                if cleaned_data.get('prix_location'):
                    cleaned_data['prix_location'] = SecurityValidator.validate_amount(cleaned_data['prix_location'])
                
                if cleaned_data.get('charges_mensuelles'):
                    cleaned_data['charges_mensuelles'] = SecurityValidator.validate_amount(cleaned_data['charges_mensuelles'])
                
                # Valider la surface
                if cleaned_data.get('surface'):
                    cleaned_data['surface'] = SecurityValidator.validate_surface(cleaned_data['surface'])
                
                # Sauvegarder avec le gestionnaire sécurisé
                propriete, success, message = DataSaveHandler.save_propriete(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Propriété ajoutée avec succès: {message}')
                    return redirect('proprietes:liste')
                else:
                    messages.error(request, f'Erreur lors de l\'ajout: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur ajouter_propriete: {e}")
    else:
        form = ProprieteForm()
    
    context = {
        'form': form,
        'bailleurs': Bailleur.objects.filter(est_actif=True),
        'locataires': Locataire.objects.filter(est_actif=True),
        'types_bien': TypeBien.objects.all(),
        'title': 'Ajouter une Propriété',
        'submit_text': 'Enregistrer la Propriété'
    }
    return render(request, 'proprietes/ajouter.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef ajouter_propriete\(request\):.*?return render\(request, \'proprietes/ajouter\.html\', context\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue ajouter_propriete mise à jour")
    else:
        print("⚠️ Vue ajouter_propriete non trouvée")


def update_modifier_propriete_view():
    """Mettre à jour la vue modifier_propriete"""
    
    content = '''@login_required
def modifier_propriete(request, pk):
    """
    Vue sécurisée pour modifier une propriété
    """
    propriete = get_object_or_404(Propriete, pk=pk)
    
    if request.method == 'POST':
        try:
            # Utiliser le formulaire sécurisé
            form = ProprieteForm(request.POST, instance=propriete)
            
            if form.is_valid():
                # Nettoyer et valider les données
                cleaned_data = form.cleaned_data
                
                # Nettoyer les données avec le sanitizer
                cleaned_data['titre'] = DataSanitizer.sanitize_text(cleaned_data['titre'])
                cleaned_data['ville'] = DataSanitizer.sanitize_name(cleaned_data['ville'])
                cleaned_data['code_postal'] = DataSanitizer.sanitize_postal_code(cleaned_data['code_postal'])
                
                # Valider les montants
                if cleaned_data.get('prix_location'):
                    cleaned_data['prix_location'] = SecurityValidator.validate_amount(cleaned_data['prix_location'])
                
                if cleaned_data.get('charges_mensuelles'):
                    cleaned_data['charges_mensuelles'] = SecurityValidator.validate_amount(cleaned_data['charges_mensuelles'])
                
                # Valider la surface
                if cleaned_data.get('surface'):
                    cleaned_data['surface'] = SecurityValidator.validate_surface(cleaned_data['surface'])
                
                # Ajouter l'ID pour la mise à jour
                cleaned_data['id'] = pk
                
                # Sauvegarder avec le gestionnaire sécurisé
                propriete, success, message = DataSaveHandler.save_propriete(cleaned_data, request.user)
                
                if success:
                    messages.success(request, f'Propriété modifiée avec succès: {message}')
                    return redirect('proprietes:detail', pk=pk)
                else:
                    messages.error(request, f'Erreur lors de la modification: {message}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                
        except ValidationError as e:
            messages.error(request, f'Erreur de validation: {e}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {e}')
            # Logger l'erreur pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur modifier_propriete: {e}")
    else:
        form = ProprieteForm(instance=propriete)
    
    context = {
        'form': form,
        'propriete': propriete,
        'bailleurs': Bailleur.objects.filter(est_actif=True),
        'locataires': Locataire.objects.filter(est_actif=True),
        'types_bien': TypeBien.objects.all(),
        'title': 'Modifier la Propriété',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'proprietes/modifier.html', context)'''
    
    # Écrire dans le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content_file = f.read()
    
    # Remplacer la fonction existante
    import re
    pattern = r'@login_required\s*\ndef modifier_propriete\(request, pk\):.*?return render\(request, \'proprietes/modifier\.html\', context\)'
    replacement = content
    
    if re.search(pattern, content_file, re.DOTALL):
        content_file = re.sub(pattern, replacement, content_file, flags=re.DOTALL)
        with open('proprietes/views.py', 'w', encoding='utf-8') as f:
            f.write(content_file)
        print("✅ Vue modifier_propriete mise à jour")
    else:
        print("⚠️ Vue modifier_propriete non trouvée")


def add_imports_to_views():
    """Ajouter les imports nécessaires au fichier views.py"""
    
    print("\n📦 Ajout des imports de sécurité")
    
    imports = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Propriete, Bailleur, Locataire, TypeBien
from .forms import BailleurForm, LocataireForm, ProprieteForm
from core.save_handlers import DataSaveHandler
from core.validators import SecurityValidator, DataSanitizer
'''
    
    # Lire le fichier views.py
    with open('proprietes/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si les imports sont déjà présents
    if 'from core.save_handlers import DataSaveHandler' not in content:
        # Remplacer les imports existants
        import re
        pattern = r'from django\.shortcuts import.*?\n'
        replacement = imports
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            with open('proprietes/views.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Imports de sécurité ajoutés")
        else:
            print("⚠️ Imports existants non trouvés")
    else:
        print("✅ Imports de sécurité déjà présents")


def main():
    """Fonction principale"""
    
    print("🚀 Mise à jour des vues avec la sécurité")
    print("=" * 60)
    
    # Ajouter les imports
    add_imports_to_views()
    
    # Mettre à jour les vues
    update_proprietes_views()
    
    print("\n🎉 Mise à jour terminée avec succès !")
    print("\n📋 Récapitulatif des améliorations:")
    print("✅ Formulaires sécurisés avec validation")
    print("✅ Nettoyage automatique des données")
    print("✅ Sauvegarde sécurisée en base")
    print("✅ Gestion d'erreurs améliorée")
    print("✅ Logging des actions")
    print("✅ Protection contre les injections")
    print("✅ Validation des montants et surfaces")


if __name__ == '__main__':
    main() 