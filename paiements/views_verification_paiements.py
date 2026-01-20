"""
Vues pour vérifier et corriger les incohérences de paiements
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
from dateutil.relativedelta import relativedelta
from contrats.models import Contrat
from .models import Paiement
import io
import sys


def is_privilege_or_admin(user):
    """Vérifie si l'utilisateur a les droits PRIVILEGE ou ADMINISTRATION"""
    return user.groups.filter(name__in=['PRIVILEGE', 'ADMINISTRATION']).exists()


@login_required
def verification_mois_paye(request):
    """
    Affiche tous les paiements avec leurs mois_paye et détecte les incohérences
    """
    # Vérification manuelle des permissions
    if not is_privilege_or_admin(request.user):
        messages.error(request, "❌ Accès refusé. Cette fonctionnalité est réservée aux groupes PRIVILEGE et ADMINISTRATION.")
        return redirect('core:dashboard')
    
    # Récupérer tous les contrats actifs
    contrats = Contrat.objects.filter(est_actif=True, is_deleted=False).order_by('numero_contrat')
    
    resultats = []
    total_incoherences = 0
    
    mois_francais = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
        'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10,
        'november': 11, 'december': 12
    }
    
    for contrat in contrats:
        # Récupérer tous les paiements de loyer pour ce contrat
        paiements = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut__in=['valide', 'confirme'],
            is_deleted=False
        ).exclude(
            Q(mois_paye__isnull=True) | Q(mois_paye='')
        ).order_by('date_paiement', 'id')
        
        if not paiements.exists():
            continue
        
        paiements_data = []
        dernier_mois_attendu = None
        contrat_a_incoherence = False
        
        for paiement in paiements:
            try:
                # Parser le mois_paye
                mois_paye_str = paiement.mois_paye
                parts = mois_paye_str.lower().split()
                
                if len(parts) < 2:
                    paiements_data.append({
                        'paiement': paiement,
                        'est_incoherent': True,
                        'message': 'Format invalide',
                        'mois_attendu': None
                    })
                    contrat_a_incoherence = True
                    total_incoherences += 1
                    continue
                
                mois_nom = parts[0]
                annee = int(parts[1])
                mois_num = mois_francais.get(mois_nom, 1)
                mois_actuel = datetime(annee, mois_num, 1).date()
                
                # Si c'est le premier paiement
                if dernier_mois_attendu is None:
                    paiements_data.append({
                        'paiement': paiement,
                        'est_incoherent': False,
                        'message': 'Premier paiement (OK)',
                        'mois_attendu': None
                    })
                    dernier_mois_attendu = mois_actuel
                else:
                    # Vérifier la séquence
                    mois_attendu = dernier_mois_attendu + relativedelta(months=1)
                    
                    if mois_actuel != mois_attendu:
                        # Incohérence détectée
                        mois_attendu_str_fr = [
                            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
                        ][mois_attendu.month - 1]
                        mois_attendu_str = f"{mois_attendu_str_fr} {mois_attendu.year}"
                        
                        paiements_data.append({
                            'paiement': paiement,
                            'est_incoherent': True,
                            'message': f'Attendu: {mois_attendu_str}',
                            'mois_attendu': mois_attendu_str
                        })
                        contrat_a_incoherence = True
                        total_incoherences += 1
                        dernier_mois_attendu = mois_attendu  # Continuer avec le mois attendu
                    else:
                        paiements_data.append({
                            'paiement': paiement,
                            'est_incoherent': False,
                            'message': 'Cohérent',
                            'mois_attendu': None
                        })
                        dernier_mois_attendu = mois_actuel
                        
            except Exception as e:
                paiements_data.append({
                    'paiement': paiement,
                    'est_incoherent': True,
                    'message': f'Erreur: {str(e)}',
                    'mois_attendu': None
                })
                contrat_a_incoherence = True
                total_incoherences += 1
        
        if paiements_data:
            resultats.append({
                'contrat': contrat,
                'paiements': paiements_data,
                'a_incoherence': contrat_a_incoherence
            })
    
    context = {
        'resultats': resultats,
        'total_incoherences': total_incoherences,
        'total_contrats': len(resultats),
    }
    
    return render(request, 'paiements/verification_mois_paye.html', context)


@login_required
def lancer_correction_mois_paye(request):
    """
    Lance la correction manuelle des mois_paye incohérents
    """
    # Vérification manuelle des permissions
    if not is_privilege_or_admin(request.user):
        messages.error(request, "❌ Accès refusé. Cette fonctionnalité est réservée aux groupes PRIVILEGE et ADMINISTRATION.")
        return redirect('core:dashboard')
    
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée")
        return redirect('paiements:verification_mois_paye')
    
    # Capturer la sortie de la commande
    output_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output_buffer
    
    try:
        from django.core.management import call_command
        
        # Lancer la commande
        call_command('corriger_mois_paye_incoherents')
        
        # Restaurer stdout
        sys.stdout = old_stdout
        output = output_buffer.getvalue()
        
        # Extraire les statistiques de la sortie
        if 'Paiements corriges:' in output:
            # Trouver le nombre de corrections
            for line in output.split('\n'):
                if 'Paiements corriges:' in line:
                    nb_corrections = line.split(':')[1].strip()
                    if int(nb_corrections) > 0:
                        messages.success(
                            request, 
                            f"✅ Correction terminée ! {nb_corrections} paiement(s) corrigé(s)."
                        )
                    else:
                        messages.info(request, "Aucune incohérence détectée.")
                    break
        else:
            messages.success(request, "✅ Correction lancée avec succès !")
        
        # Stocker la sortie complète dans la session pour affichage
        request.session['correction_output'] = output
        
    except Exception as e:
        sys.stdout = old_stdout
        messages.error(request, f"❌ Erreur lors de la correction : {str(e)}")
    
    return redirect('paiements:verification_mois_paye')


@login_required
def afficher_logs_correction(request):
    """
    Affiche les logs de la dernière correction
    """
    # Vérification manuelle des permissions
    if not is_privilege_or_admin(request.user):
        messages.error(request, "❌ Accès refusé. Cette fonctionnalité est réservée aux groupes PRIVILEGE et ADMINISTRATION.")
        return redirect('core:dashboard')
    
    output = request.session.get('correction_output', '')
    
    if not output:
        messages.info(request, "Aucun log disponible. Lancez une correction d'abord.")
        return redirect('paiements:verification_mois_paye')
    
    context = {
        'logs': output,
    }
    
    return render(request, 'paiements/logs_correction_mois_paye.html', context)
