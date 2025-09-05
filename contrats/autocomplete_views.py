from dal import autocomplete
from proprietes.models import Propriete, UniteLocative
from utilisateurs.models import Locataire

class ProprieteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Propriete.objects.all()
        if self.q:
            qs = qs.filter(titre__icontains=self.q) | qs.filter(numero_propriete__icontains=self.q)
        return qs

class LocataireAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Locataire.objects.all()
        if self.q:
            qs = qs.filter(nom__icontains=self.q) | qs.filter(prenom__icontains=self.q)
        return qs

class UniteLocativeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = UniteLocative.objects.all()
        if self.q:
            qs = qs.filter(nom__icontains=self.q)
        return qs
