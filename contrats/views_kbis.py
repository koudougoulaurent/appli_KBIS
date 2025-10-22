from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
import weasyprint
import io
from datetime import datetime, timedelta

from .models import Contrat
from .models_kbis import ContratKbis, EtatLieuxKbis
from .utils import generer_numero_contrat_kbis, calculer_caution_automatique
from proprietes.models import Locataire, Propriete


@login_required
def creer_contrat_kbis(request, contrat_id):
    """
    Crée un contrat KBIS à partir d'un contrat existant.
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    # Vérifier si un contrat KBIS existe déjà
    if hasattr(contrat, 'contrat_kbis'):
        messages.info(request, "Un contrat KBIS existe déjà pour ce contrat.")
        return redirect('contrats:detail_contrat_kbis', contrat_id=contrat.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Créer le contrat KBIS
                contrat_kbis = ContratKbis.objects.create(
                    contrat=contrat,
                    locataire_cnib=request.POST.get('locataire_cnib', ''),
                    locataire_profession=request.POST.get('locataire_profession', ''),
                    locataire_adresse=request.POST.get('locataire_adresse', ''),
                    locataire_telephone=request.POST.get('locataire_telephone', ''),
                    garant_nom=request.POST.get('garant_nom', ''),
                    garant_profession=request.POST.get('garant_profession', ''),
                    garant_adresse=request.POST.get('garant_adresse', ''),
                    garant_telephone=request.POST.get('garant_telephone', ''),
                    garant_cnib=request.POST.get('garant_cnib', ''),
                    propriete_numero=request.POST.get('propriete_numero', ''),
                    propriete_adresse=request.POST.get('propriete_adresse', ''),
                    caution_montant=calculer_caution_automatique(contrat.loyer_mensuel),
                    paiement_debut_mois=request.POST.get('paiement_debut_mois', 'fin du mois de SEPTEMBRE 2025'),
                    paiement_echeance=request.POST.get('paiement_echeance', '03 du mois suivant'),
                    delai_annulation=int(request.POST.get('delai_annulation', 48)),
                    preavis_resiliation_locataire=request.POST.get('preavis_resiliation_locataire', 'un mois'),
                    preavis_resiliation_agence=request.POST.get('preavis_resiliation_agence', 'trois mois'),
                    date_remise_cles=request.POST.get('date_remise_cles', '01er du mois suivant')
                )
                
                # Créer l'état des lieux
                etat_lieux = EtatLieuxKbis.objects.create(
                    contrat_kbis=contrat_kbis,
                    indexe_sonabel=request.POST.get('indexe_sonabel') == 'on',
                    indexe_onea=request.POST.get('indexe_onea') == 'on',
                    peinture_murs=request.POST.get('peinture_murs', 'OK'),
                    peinture_couvertures=request.POST.get('peinture_couvertures', 'OK'),
                    peinture_plafond=request.POST.get('peinture_plafond', 'OK'),
                    cremone_vitre=request.POST.get('cremone_vitre', 'OK'),
                    prise_electrique=request.POST.get('prise_electrique', 'OK'),
                    cles_grand_portail=request.POST.get('cles_grand_portail') == 'on',
                    cles_porte_salon=request.POST.get('cles_porte_salon') == 'on',
                    cles_iso_planes=request.POST.get('cles_iso_planes') == 'on',
                    cles_placard=request.POST.get('cles_placard') == 'on',
                    porte_rideau=request.POST.get('porte_rideau') == 'on',
                    reglettes=request.POST.get('reglettes', 'OK'),
                    veilleuses=request.POST.get('veilleuses', 'OK'),
                    ventilateurs=request.POST.get('ventilateurs', 'OK'),
                    robinets_cuisine=request.POST.get('robinets_cuisine', 'OK'),
                    placards_cuisine=request.POST.get('placards_cuisine', 'OK'),
                    sonnerie=request.POST.get('sonnerie', 'OK'),
                    wc=request.POST.get('wc', 'OK'),
                    lavabos=request.POST.get('lavabos', 'OK'),
                    miroir=request.POST.get('miroir', 'OK'),
                    flexible_douche=request.POST.get('flexible_douche', 'OK'),
                    accessoires_sanitaires=request.POST.get('accessoires_sanitaires', 'OK'),
                    lampes_sanitaire=request.POST.get('lampes_sanitaire', 'OK'),
                    chauffe_eau=request.POST.get('chauffe_eau', 'OK'),
                    climatiseur=request.POST.get('climatiseur', 'OK'),
                    observations=request.POST.get('observations', '')
                )
                
                messages.success(request, "Contrat KBIS créé avec succès !")
                return redirect('contrats:detail_contrat_kbis', contrat_id=contrat.id)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du contrat KBIS : {str(e)}")
    
    # Pré-remplir les données du locataire et de la propriété
    context = {
        'contrat': contrat,
        'locataire': contrat.locataire,
        'propriete': contrat.propriete,
        'loyer_mensuel': contrat.loyer_mensuel,
        'caution_automatique': calculer_caution_automatique(contrat.loyer_mensuel)
    }
    
    return render(request, 'contrats/creer_contrat_kbis.html', context)


@login_required
def detail_contrat_kbis(request, contrat_id):
    """
    Affiche les détails d'un contrat KBIS.
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    try:
        contrat_kbis = contrat.contrat_kbis
    except ContratKbis.DoesNotExist:
        messages.error(request, "Aucun contrat KBIS trouvé pour ce contrat.")
        return redirect('contrats:liste')
    
    context = {
        'contrat': contrat,
        'contrat_kbis': contrat_kbis,
        'etat_lieux': getattr(contrat_kbis, 'etat_lieux', None)
    }
    
    return render(request, 'contrats/detail_contrat_kbis.html', context)


@login_required
def generer_pdf_contrat_kbis(request, contrat_id):
    """
    Génère le PDF du contrat KBIS.
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    try:
        contrat_kbis = contrat.contrat_kbis
    except ContratKbis.DoesNotExist:
        messages.error(request, "Aucun contrat KBIS trouvé pour ce contrat.")
        return redirect('contrats:liste')
    
    # Rendre le template HTML
    html_string = render_to_string('contrats/contrat_kbis.html', {
        'contrat': contrat,
        'contrat_kbis': contrat_kbis,
        'etat_lieux': getattr(contrat_kbis, 'etat_lieux', None)
    })
    
    # Générer le PDF
    try:
        pdf_file = weasyprint.HTML(string=html_string).write_pdf()
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrat_kbis_{contrat.numero_contrat}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF : {str(e)}")
        return redirect('contrats:detail_contrat_kbis', contrat_id=contrat.id)


@login_required
def modifier_contrat_kbis(request, contrat_id):
    """
    Modifie un contrat KBIS existant.
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    try:
        contrat_kbis = contrat.contrat_kbis
    except ContratKbis.DoesNotExist:
        messages.error(request, "Aucun contrat KBIS trouvé pour ce contrat.")
        return redirect('contrats:liste')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mettre à jour le contrat KBIS
                contrat_kbis.locataire_cnib = request.POST.get('locataire_cnib', '')
                contrat_kbis.locataire_profession = request.POST.get('locataire_profession', '')
                contrat_kbis.locataire_adresse = request.POST.get('locataire_adresse', '')
                contrat_kbis.locataire_telephone = request.POST.get('locataire_telephone', '')
                contrat_kbis.garant_nom = request.POST.get('garant_nom', '')
                contrat_kbis.garant_profession = request.POST.get('garant_profession', '')
                contrat_kbis.garant_adresse = request.POST.get('garant_adresse', '')
                contrat_kbis.garant_telephone = request.POST.get('garant_telephone', '')
                contrat_kbis.garant_cnib = request.POST.get('garant_cnib', '')
                contrat_kbis.propriete_numero = request.POST.get('propriete_numero', '')
                contrat_kbis.propriete_adresse = request.POST.get('propriete_adresse', '')
                contrat_kbis.caution_montant = float(request.POST.get('caution_montant', 0))
                contrat_kbis.paiement_debut_mois = request.POST.get('paiement_debut_mois', '')
                contrat_kbis.paiement_echeance = request.POST.get('paiement_echeance', '')
                contrat_kbis.delai_annulation = int(request.POST.get('delai_annulation', 48))
                contrat_kbis.preavis_resiliation_locataire = request.POST.get('preavis_resiliation_locataire', '')
                contrat_kbis.preavis_resiliation_agence = request.POST.get('preavis_resiliation_agence', '')
                contrat_kbis.date_remise_cles = request.POST.get('date_remise_cles', '')
                contrat_kbis.save()
                
                # Mettre à jour l'état des lieux
                if hasattr(contrat_kbis, 'etat_lieux'):
                    etat_lieux = contrat_kbis.etat_lieux
                    etat_lieux.indexe_sonabel = request.POST.get('indexe_sonabel') == 'on'
                    etat_lieux.indexe_onea = request.POST.get('indexe_onea') == 'on'
                    etat_lieux.peinture_murs = request.POST.get('peinture_murs', 'OK')
                    etat_lieux.peinture_couvertures = request.POST.get('peinture_couvertures', 'OK')
                    etat_lieux.peinture_plafond = request.POST.get('peinture_plafond', 'OK')
                    etat_lieux.cremone_vitre = request.POST.get('cremone_vitre', 'OK')
                    etat_lieux.prise_electrique = request.POST.get('prise_electrique', 'OK')
                    etat_lieux.cles_grand_portail = request.POST.get('cles_grand_portail') == 'on'
                    etat_lieux.cles_porte_salon = request.POST.get('cles_porte_salon') == 'on'
                    etat_lieux.cles_iso_planes = request.POST.get('cles_iso_planes') == 'on'
                    etat_lieux.cles_placard = request.POST.get('cles_placard') == 'on'
                    etat_lieux.porte_rideau = request.POST.get('porte_rideau') == 'on'
                    etat_lieux.reglettes = request.POST.get('reglettes', 'OK')
                    etat_lieux.veilleuses = request.POST.get('veilleuses', 'OK')
                    etat_lieux.ventilateurs = request.POST.get('ventilateurs', 'OK')
                    etat_lieux.robinets_cuisine = request.POST.get('robinets_cuisine', 'OK')
                    etat_lieux.placards_cuisine = request.POST.get('placards_cuisine', 'OK')
                    etat_lieux.sonnerie = request.POST.get('sonnerie', 'OK')
                    etat_lieux.wc = request.POST.get('wc', 'OK')
                    etat_lieux.lavabos = request.POST.get('lavabos', 'OK')
                    etat_lieux.miroir = request.POST.get('miroir', 'OK')
                    etat_lieux.flexible_douche = request.POST.get('flexible_douche', 'OK')
                    etat_lieux.accessoires_sanitaires = request.POST.get('accessoires_sanitaires', 'OK')
                    etat_lieux.lampes_sanitaire = request.POST.get('lampes_sanitaire', 'OK')
                    etat_lieux.chauffe_eau = request.POST.get('chauffe_eau', 'OK')
                    etat_lieux.climatiseur = request.POST.get('climatiseur', 'OK')
                    etat_lieux.observations = request.POST.get('observations', '')
                    etat_lieux.save()
                
                messages.success(request, "Contrat KBIS modifié avec succès !")
                return redirect('contrats:detail_contrat_kbis', contrat_id=contrat.id)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification du contrat KBIS : {str(e)}")
    
    context = {
        'contrat': contrat,
        'contrat_kbis': contrat_kbis,
        'etat_lieux': getattr(contrat_kbis, 'etat_lieux', None)
    }
    
    return render(request, 'contrats/modifier_contrat_kbis.html', context)


@login_required
def liste_contrats_kbis(request):
    """
    Liste tous les contrats KBIS.
    """
    contrats_kbis = ContratKbis.objects.select_related(
        'contrat__locataire',
        'contrat__propriete'
    ).order_by('-date_generation')
    
    context = {
        'contrats_kbis': contrats_kbis
    }
    
    return render(request, 'contrats/liste_contrats_kbis.html', context)
