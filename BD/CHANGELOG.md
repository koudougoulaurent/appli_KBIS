
# 📝 Changelog - Documentation BD

## 23/09/2025 - Suppression de "INTERNATIONAL"

### Modifications apportées :
- ✅ Remplacement de "KBIS INTERNATIONAL" par "KBIS IMMOBILIER" dans toute la documentation
- ✅ Mise à jour des templates pour utiliser la configuration dynamique de l'entreprise
- ✅ Ajout du processeur de contexte entreprise_config
- ✅ Modification de la base de données : nom_entreprise = 'KBIS IMMOBILIER'

### Fichiers modifiés :
- `core/context_processors.py` - Ajout du processeur entreprise_config
- `templates/utilisateurs/connexion_groupes.html` - Utilisation de la variable dynamique
- `gestion_immobiliere/settings.py` - Configuration du context processor
- Base de données : `core_configurationentreprise.nom_entreprise`

### Impact :
- L'interface utilisateur affiche maintenant "KBIS IMMOBILIER" au lieu de "KBIS INTERNATIONAL"
- Le nom de l'entreprise est récupéré dynamiquement depuis la configuration
- Plus de cohérence dans l'identité visuelle de l'application

---
*Changelog généré automatiquement le 23/09/2025 à 21:13*
