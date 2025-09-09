"""
Mixins pour l'intégration automatique des actions rapides
"""

from core.quick_actions_generator import QuickActionsGenerator

class QuickActionsMixin:
    """Mixin pour ajouter automatiquement les actions rapides aux vues"""
    
    def get_quick_actions(self, context):
        """Génère les actions rapides selon le contexte"""
        return QuickActionsGenerator.get_actions_for_context(context, self.request)
    
    def get_context_data(self, **kwargs):
        """Ajoute les actions rapides au contexte"""
        context = super().get_context_data(**kwargs)
        context['quick_actions'] = self.get_quick_actions(context)
        return context

class DetailViewQuickActionsMixin(QuickActionsMixin):
    """Mixin spécialisé pour les vues de détail"""
    
    def get_quick_actions(self, context):
        """Actions rapides pour les vues de détail"""
        # Récupérer l'objet principal de la vue
        obj = getattr(self, 'object', None)
        if not obj and hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
            except:
                obj = None
        
        if obj:
            # Déterminer le type d'objet et générer les actions appropriées
            obj_name = obj.__class__.__name__.lower()
            context[obj_name] = obj
            
        return super().get_quick_actions(context)

class ListViewQuickActionsMixin(QuickActionsMixin):
    """Mixin spécialisé pour les vues de liste"""
    
    def get_quick_actions(self, context):
        """Actions rapides pour les vues de liste"""
        # Actions générales selon le modèle
        model_name = self.model.__name__.lower()
        
        if 'bailleur' in model_name:
            context['bailleur'] = None  # Pas d'objet spécifique
        elif 'locataire' in model_name:
            context['locataire'] = None
        elif 'propriete' in model_name:
            context['propriete'] = None
        elif 'contrat' in model_name:
            context['contrat'] = None
        elif 'paiement' in model_name:
            context['paiement'] = None
            
        return super().get_quick_actions(context)
