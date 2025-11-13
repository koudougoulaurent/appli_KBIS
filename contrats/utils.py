"""
Utilitaires pour les contrats KBIS
"""

def nombre_en_lettres(nombre):
    """
    Convertit un nombre en lettres (français).
    """
    if nombre == 0:
        return "zéro"
    
    # Dictionnaires pour la conversion
    unites = {
        0: "", 1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
        6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix",
        11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
        16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf"
    }
    
    dizaines = {
        2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante",
        6: "soixante", 7: "soixante-dix", 8: "quatre-vingt", 9: "quatre-vingt-dix"
    }
    
    centaines = {
        1: "cent", 2: "deux cents", 3: "trois cents", 4: "quatre cents",
        5: "cinq cents", 6: "six cents", 7: "sept cents", 8: "huit cents", 9: "neuf cents"
    }
    
    milliers = {
        1: "mille", 2: "deux mille", 3: "trois mille", 4: "quatre mille",
        5: "cinq mille", 6: "six mille", 7: "sept mille", 8: "huit mille", 9: "neuf mille"
    }
    
    def convertir_centaines(n):
        """Convertit les centaines."""
        if n < 100:
            return convertir_dizaines(n)
        
        centaine = n // 100
        reste = n % 100
        
        if centaine == 1:
            if reste == 0:
                return "cent"
            else:
                return f"cent {convertir_dizaines(reste)}"
        else:
            if reste == 0:
                return centaines[centaine]
            else:
                return f"{centaines[centaine]} {convertir_dizaines(reste)}"
    
    def convertir_dizaines(n):
        """Convertit les dizaines."""
        if n < 20:
            return unites[n]
        
        dizaine = n // 10
        unite = n % 10
        
        if dizaine == 7:  # 70-79
            if unite == 1:
                return "soixante et onze"
            elif unite == 0:
                return "soixante-dix"
            else:
                return f"soixante-{unites[unite + 10]}"
        elif dizaine == 9:  # 90-99
            if unite == 1:
                return "quatre-vingt-onze"
            elif unite == 0:
                return "quatre-vingt-dix"
            else:
                return f"quatre-vingt-{unites[unite + 10]}"
        elif dizaine == 8:  # 80-89
            if unite == 0:
                return "quatre-vingts"
            else:
                return f"quatre-vingt-{unites[unite]}"
        else:
            if unite == 0:
                return dizaines[dizaine]
            elif unite == 1 and dizaine != 8:
                return f"{dizaines[dizaine]} et un"
            else:
                return f"{dizaines[dizaine]}-{unites[unite]}"
    
    def convertir_milliers(n):
        """Convertit les milliers."""
        if n < 1000:
            return convertir_centaines(n)
        
        millier = n // 1000
        reste = n % 1000
        
        if millier == 1:
            if reste == 0:
                return "mille"
            else:
                return f"mille {convertir_centaines(reste)}"
        else:
            if reste == 0:
                return milliers[millier]
            else:
                return f"{milliers[millier]} {convertir_centaines(reste)}"
    
    # Conversion principale
    if nombre < 1000:
        return convertir_centaines(nombre)
    elif nombre < 1000000:
        return convertir_milliers(nombre)
    else:
        # Pour les nombres plus grands, on peut étendre si nécessaire
        return str(nombre)


def formater_montant_lettres(montant):
    """
    Formate un montant en lettres avec "Francs CFA".
    """
    montant_entier = int(montant)
    montant_lettres = nombre_en_lettres(montant_entier)
    
    if montant_entier == 1:
        return f"{montant_lettres.upper()} Franc CFA"
    else:
        return f"{montant_lettres.upper()} Francs CFA"


def formater_mois_lettres(mois):
    """
    Convertit un numéro de mois en lettres.
    """
    mois_lettres = {
        1: "JANVIER", 2: "FÉVRIER", 3: "MARS", 4: "AVRIL",
        5: "MAI", 6: "JUIN", 7: "JUILLET", 8: "AOÛT",
        9: "SEPTEMBRE", 10: "OCTOBRE", 11: "NOVEMBRE", 12: "DÉCEMBRE"
    }
    return mois_lettres.get(mois, str(mois))


def formater_date_lettres(date):
    """
    Formate une date en lettres.
    """
    from datetime import datetime
    
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    jour = date.day
    mois = formater_mois_lettres(date.month)
    annee = date.year
    
    return f"{jour} {mois} {annee}"


def generer_numero_contrat_kbis():
    """
    Génère un numéro de contrat KBIS unique.
    """
    from datetime import datetime
    import random
    
    # Format: KBIS-YYYY-MM-NNNN
    now = datetime.now()
    annee = now.year
    mois = now.month
    numero = random.randint(1000, 9999)
    
    return f"KBIS-{annee}-{mois:02d}-{numero}"


def calculer_caution_automatique(loyer_mensuel, nombre_mois=3):
    """
    Calcule automatiquement le montant de la caution.
    """
    return loyer_mensuel * nombre_mois


def get_proprietes_disponibles():
    """
    Retourne les propriétés disponibles pour la création de contrats.
    Une propriété est disponible si :
    1. Pour les propriétés avec unités locatives : elle a au moins une unité locative disponible
    2. Pour les propriétés entières (sans unités) : elle n'a pas de contrat actif qui couvre la propriété entière ET elle est marquée comme disponible
    CORRIGÉ : Prend en compte les unités locatives disponibles même si d'autres unités de la même propriété sont occupées
    """
    from proprietes.models import Propriete
    from proprietes.models import UniteLocative
    from .models import Contrat
    from django.db.models import Q, Exists, OuterRef
    
    # 1. PROPRIÉTÉS AVEC UNITÉS LOCATIVES DISPONIBLES
    # Une propriété avec unités locatives est disponible si elle a au moins une unité disponible
    # (même si d'autres unités de la même propriété sont occupées)
    proprietes_avec_unites_disponibles = Propriete.objects.filter(
        unites_locatives__statut='disponible',
        unites_locatives__is_deleted=False
    ).distinct()
    
    # 2. PROPRIÉTÉS ENTIÈRES (SANS UNITÉS LOCATIVES) DISPONIBLES
    # Une propriété entière est disponible si :
    # - Elle est marquée comme disponible
    # - Elle n'a pas de contrat actif qui couvre la propriété entière (sans unité_locative)
    proprietes_entières = Propriete.objects.filter(
        disponible=True,
        unites_locatives__isnull=True
    )
    
    # Exclure les propriétés entières qui ont des contrats actifs (sans unité_locative)
    contrats_actifs_propriete_entiere = Contrat.all_objects.filter(
        propriete=OuterRef('pk'),
        est_actif=True,
        est_resilie=False,
        unite_locative__isnull=True  # Contrat qui couvre la propriété entière
    )
    
    proprietes_entières_disponibles = proprietes_entières.exclude(
        Exists(contrats_actifs_propriete_entiere)
    )
    
    # 3. COMBINER LES DEUX TYPES DE PROPRIÉTÉS
    # Utiliser une union pour combiner les deux querysets
    proprietes_ids_avec_unites = list(proprietes_avec_unites_disponibles.values_list('pk', flat=True))
    proprietes_ids_entières = list(proprietes_entières_disponibles.values_list('pk', flat=True))
    
    # Combiner les IDs uniques
    tous_ids = list(set(proprietes_ids_avec_unites + proprietes_ids_entières))
    
    # Retourner les propriétés dans l'ordre
    if tous_ids:
        return Propriete.objects.filter(pk__in=tous_ids).order_by('titre')
    else:
        return Propriete.objects.none()