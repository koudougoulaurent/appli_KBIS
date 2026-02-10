#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import ChargesBailleur
from datetime import date

charges = ChargesBailleur.objects.all()
print(f'Total charges dans la base: {charges.count()}')

charges_fev = ChargesBailleur.objects.filter(date_charge__year=2026, date_charge__month=2)
print(f'Charges février 2026: {charges_fev.count()}')

if charges.exists():
    derniere = charges.order_by('-date_charge').first()
    print(f'\nDernière charge: {derniere.date_charge} - {derniere.montant} F CFA ({derniere.titre})')
    
    # Compter par mois
    from django.db.models import Count, Sum
    charges_par_mois = ChargesBailleur.objects.values('date_charge__year', 'date_charge__month').annotate(
        total=Sum('montant'),
        count=Count('id')
    ).order_by('-date_charge__year', '-date_charge__month')[:5]
    
    print('\nDerniers mois avec charges:')
    for item in charges_par_mois:
        print(f"  {item['date_charge__month']}/{item['date_charge__year']}: {item['count']} charges, total: {item['total']} F CFA")
else:
    print('\n⚠️ Aucune charge dans la base de données!')
    print('Les charges doivent être créées depuis l\'interface admin.')
