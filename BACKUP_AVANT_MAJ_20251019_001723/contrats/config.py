# Configuration des contrats et résiliations
# ATTENTION: Ce fichier n'est plus utilisé depuis la version 2.0
# La configuration se fait maintenant via la base de données via le modèle ConfigurationEntreprise
# 
# Pour personnaliser les informations de l'entreprise, allez dans :
# Core > Configuration de l'entreprise

# Ce fichier est conservé pour référence historique uniquement
# Les services PDF utilisent maintenant ConfigurationEntreprise.get_configuration_active()

# Configuration par défaut (fallback si pas de configuration en base)
ENTREPRISE_CONFIG_DEFAUT = {
    'nom': 'GESTIMMOB',
    'adresse': '123 Rue de la Paix',
    'ville': 'Paris',
    'code_postal': '75001',
    'pays': 'France',
    'telephone': '01 23 45 67 89',
    'email': 'contact@gestimmob.fr',
    'siret': '123 456 789 00012',
}

# Configuration des PDF (styles et mise en page)
PDF_CONFIG = {
    'format_page': 'A4',
    'marges': {
        'gauche': 2.0, 'droite': 2.0, 'haut': 2.0, 'bas': 2.0
    },
    'polices': {
        'titre_principal': 'Helvetica-Bold', 'titre_secondaire': 'Helvetica-Bold',
        'corps': 'Helvetica', 'signature': 'Helvetica'
    },
    'couleurs': {
        'titre': '#2c3e50', 'texte': '#000000', 'accent': '#3498db'
    },
    'espacement': {
        'section': 20, 'paragraphe': 10, 'ligne': 6
    }
}

# Clauses contractuelles par défaut (si pas de configuration personnalisée)
CLAUSES_CONTRACTUELLES_DEFAUT = """
Obligations du locataire :
• Payer le loyer et les charges dans les délais convenus
• Entretenir les lieux loués
• Respecter le règlement intérieur
• Ne pas effectuer de travaux sans autorisation
• Assurer le logement contre les risques locatifs
• Respecter la destination des lieux

Obligations du bailleur :
• Livrer le logement en bon état d'usage
• Effectuer les réparations locatives
• Respecter les obligations de sécurité
• Garantir la jouissance paisible des lieux
"""

# Modèle de résiliation par défaut (si pas de configuration personnalisée)
MODELE_RESILIATION_DEFAUT = """
Conditions de sortie :
• Le locataire doit libérer les lieux dans l'état où il les a reçus
• Un état des lieux de sortie sera effectué
• La caution sera restituée après déduction des éventuels dommages
• Les clés doivent être remises le jour de la sortie
"""
