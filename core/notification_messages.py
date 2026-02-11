"""
Messages de notification personnalisés et contextuels
Auto-dismiss après 5 secondes avec barre de progression
"""

from django.contrib import messages as django_messages


class NotificationMessages:
    """Helper pour créer des messages de notification élégants"""
    
    # Messages de succès
    @staticmethod
    def paiement_cree(request, montant, contrat):
        django_messages.success(
            request,
            f"✅ <strong>Paiement enregistré avec succès !</strong><br>"
            f"<small>Montant: {montant:,.0f} F CFA pour {contrat}</small>"
        )
    
    @staticmethod
    def contrat_cree(request, contrat):
        django_messages.success(
            request,
            f"🎉 <strong>Nouveau contrat créé !</strong><br>"
            f"<small>{contrat} est maintenant actif</small>"
        )
    
    @staticmethod
    def contrat_modifie(request, contrat):
        django_messages.success(
            request,
            f"✏️ <strong>Contrat mis à jour</strong><br>"
            f"<small>{contrat} - Modifications enregistrées</small>"
        )
    
    @staticmethod
    def propriete_creee(request, propriete):
        django_messages.success(
            request,
            f"🏠 <strong>Propriété ajoutée !</strong><br>"
            f"<small>{propriete} est disponible pour location</small>"
        )
    
    @staticmethod
    def recapitulatif_genere(request, mois, annee, bailleur=None):
        info_bailleur = f" pour {bailleur}" if bailleur else ""
        django_messages.success(
            request,
            f"📊 <strong>Récapitulatif généré avec succès</strong><br>"
            f"<small>{mois}/{annee}{info_bailleur}</small>"
        )
    
    @staticmethod
    def pdf_genere(request, type_doc="document"):
        django_messages.success(
            request,
            f"📄 <strong>PDF généré !</strong><br>"
            f"<small>Votre {type_doc} est prêt</small>"
        )
    
    @staticmethod
    def statistiques_exportees(request, format_export="CSV"):
        django_messages.success(
            request,
            f"📥 <strong>Export {format_export} réussi !</strong><br>"
            f"<small>Vos données ont été téléchargées</small>"
        )
    
    @staticmethod
    def synchronisation_reussie(request, nb_elements):
        django_messages.success(
            request,
            f"🔄 <strong>Synchronisation terminée !</strong><br>"
            f"<small>{nb_elements} élément{'s' if nb_elements > 1 else ''} synchronisé{'s' if nb_elements > 1 else ''}</small>"
        )
    
    @staticmethod
    def suppression_reussie(request, element, nb=1):
        pluriel = "s" if nb > 1 else ""
        django_messages.success(
            request,
            f"🗑️ <strong>Suppression effectuée</strong><br>"
            f"<small>{nb} {element}{pluriel} supprimé{pluriel}</small>"
        )
    
    # Messages d'information
    @staticmethod
    def calcul_en_cours(request, operation="Calcul"):
        django_messages.info(
            request,
            f"⏳ <strong>{operation} en cours...</strong><br>"
            f"<small>Veuillez patienter quelques instants</small>"
        )
    
    @staticmethod
    def aucune_modification(request):
        django_messages.info(
            request,
            f"ℹ️ <strong>Aucune modification détectée</strong><br>"
            f"<small>Les données sont déjà à jour</small>"
        )
    
    @staticmethod
    def donnees_chargees(request, nb_elements, type_element="éléments"):
        django_messages.info(
            request,
            f"📋 <strong>{nb_elements} {type_element} chargé{'s' if nb_elements > 1 else ''}</strong><br>"
            f"<small>Données prêtes à l'emploi</small>"
        )
    
    # Messages d'avertissement
    @staticmethod
    def champs_manquants(request, champs):
        liste_champs = ", ".join(champs)
        django_messages.warning(
            request,
            f"⚠️ <strong>Informations incomplètes</strong><br>"
            f"<small>Champs requis: {liste_champs}</small>"
        )
    
    @staticmethod
    def retard_paiement(request, contrat, nb_mois):
        django_messages.warning(
            request,
            f"⏰ <strong>Retard de paiement détecté</strong><br>"
            f"<small>{contrat} - {nb_mois} mois de retard</small>"
        )
    
    @staticmethod
    def contrat_expire_bientot(request, contrat, jours_restants):
        django_messages.warning(
            request,
            f"📅 <strong>Contrat expire bientôt</strong><br>"
            f"<small>{contrat} - Plus que {jours_restants} jour{'s' if jours_restants > 1 else ''}</small>"
        )
    
    @staticmethod
    def limite_atteinte(request, limite, element="éléments"):
        django_messages.warning(
            request,
            f"⚡ <strong>Limite atteinte</strong><br>"
            f"<small>Maximum {limite} {element} par opération</small>"
        )
    
    # Messages d'erreur
    @staticmethod
    def erreur_generale(request, details=""):
        message = f"❌ <strong>Une erreur s'est produite</strong>"
        if details:
            message += f"<br><small>{details}</small>"
        django_messages.error(request, message)
    
    @staticmethod
    def element_introuvable(request, element_type="élément"):
        django_messages.error(
            request,
            f"🔍 <strong>{element_type.capitalize()} introuvable</strong><br>"
            f"<small>Vérifiez vos paramètres et réessayez</small>"
        )
    
    @staticmethod
    def permission_refusee(request, action="effectuer cette action"):
        django_messages.error(
            request,
            f"🔒 <strong>Accès refusé</strong><br>"
            f"<small>Vous n'avez pas la permission de {action}</small>"
        )
    
    @staticmethod
    def montant_invalide(request, raison=""):
        message = f"💰 <strong>Montant invalide</strong>"
        if raison:
            message += f"<br><small>{raison}</small>"
        django_messages.error(request, message)
    
    @staticmethod
    def erreur_validation(request, erreurs):
        if isinstance(erreurs, list):
            liste_erreurs = "<br>".join([f"• {e}" for e in erreurs[:3]])
            if len(erreurs) > 3:
                liste_erreurs += f"<br>• ... et {len(erreurs) - 3} autre{'s' if len(erreurs) - 3 > 1 else ''}"
        else:
            liste_erreurs = str(erreurs)
        
        django_messages.error(
            request,
            f"📝 <strong>Erreurs de validation</strong><br>"
            f"<small>{liste_erreurs}</small>"
        )
    
    # Messages personnalisés pour statistiques
    @staticmethod
    def statistiques_mises_a_jour(request, periode):
        django_messages.success(
            request,
            f"📈 <strong>Statistiques actualisées !</strong><br>"
            f"<small>Données de {periode} chargées</small>"
        )
    
    @staticmethod
    def periode_changee(request, nouvelle_periode):
        django_messages.info(
            request,
            f"📆 <strong>Période modifiée</strong><br>"
            f"<small>Affichage: {nouvelle_periode}</small>"
        )


# Alias pour faciliter l'utilisation
notify = NotificationMessages
