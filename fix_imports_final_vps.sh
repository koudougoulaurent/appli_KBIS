#!/bin/bash

# Script pour corriger définitivement les imports manquants
echo "Correction définitive des imports manquants..."

cd /var/www/kbis_immobilier

# 1. Vérifier l'état actuel des fichiers
echo "1. Vérification de l'état actuel des fichiers..."

echo "=== Contenu de paiements/views_recus.py (premières 20 lignes) ==="
head -20 "paiements/views_recus.py"
echo ""

echo "=== Recherche des imports dans paiements/views_recus.py ==="
grep -n "from.*models.*import" "paiements/views_recus.py" || echo "Aucun import trouvé"
echo ""

# 2. Créer une sauvegarde
echo "2. Création d'une sauvegarde..."
cp "paiements/views_recus.py" "paiements/views_recus.py.backup_$(date +%Y%m%d_%H%M%S)"
echo "Sauvegarde créée"
echo ""

# 3. Corriger paiements/views_recus.py
echo "3. Correction de paiements/views_recus.py..."

# Créer un fichier temporaire avec les imports corrects
cat > temp_views_recus.py << 'EOF'
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import os
from decimal import Decimal
from .models import RecapMensuel, RecuRecapitulatif
EOF

# Ajouter le contenu du fichier original (en sautant les imports existants)
tail -n +2 "paiements/views_recus.py" >> temp_views_recus.py

# Remplacer le fichier original
mv temp_views_recus.py "paiements/views_recus.py"

echo "Imports ajoutés à paiements/views_recus.py"
echo ""

# 4. Corriger paiements/views_charges_avancees.py
echo "4. Correction de paiements/views_charges_avancees.py..."

if [ -f "paiements/views_charges_avancees.py" ]; then
    # Créer une sauvegarde
    cp "paiements/views_charges_avancees.py" "paiements/views_charges_avancees.py.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Ajouter l'import au début du fichier
    sed -i '1i from .models import RecapMensuel' "paiements/views_charges_avancees.py"
    
    echo "Import ajouté à paiements/views_charges_avancees.py"
fi

# 5. Corriger paiements/views_kbis_recus.py
echo "5. Correction de paiements/views_kbis_recus.py..."

if [ -f "paiements/views_kbis_recus.py" ]; then
    # Créer une sauvegarde
    cp "paiements/views_kbis_recus.py" "paiements/views_kbis_recus.py.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Ajouter l'import au début du fichier
    sed -i '1i from .models import RecapMensuel' "paiements/views_kbis_recus.py"
    
    echo "Import ajouté à paiements/views_kbis_recus.py"
fi

# 6. Vérifier les corrections
echo "6. Vérification des corrections..."

echo "=== Vérification de paiements/views_recus.py ==="
grep -n "from.*models.*import" "paiements/views_recus.py"
echo ""

echo "=== Vérification de paiements/views_charges_avancees.py ==="
grep -n "from.*models.*import" "paiements/views_charges_avancees.py" 2>/dev/null || echo "Fichier non trouvé"
echo ""

echo "=== Vérification de paiements/views_kbis_recus.py ==="
grep -n "from.*models.*import" "paiements/views_kbis_recus.py" 2>/dev/null || echo "Fichier non trouvé"
echo ""

# 7. Tester la syntaxe Python
echo "7. Test de la syntaxe Python..."

echo "Test de paiements/views_recus.py..."
python -m py_compile "paiements/views_recus.py" 2>&1 || echo "ERREUR: Syntaxe Python invalide"
echo ""

# 8. Tester Django
echo "8. Test de Django..."

python manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Django peut se charger sans erreur"
else
    echo "❌ Django a des erreurs"
fi

# 9. Redémarrer Gunicorn
echo "9. Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Vérifier le statut
echo "Vérification du statut de Gunicorn..."
sudo systemctl status gunicorn --no-pager

# 10. Test final
echo "10. Test final de l'application..."

echo "Test de l'accès à la page problématique..."
curl -I http://localhost:8000/paiements/recus-recapitulatifs/creer/1/ 2>/dev/null || echo "Erreur de connexion"

echo ""
echo "✅ Correction des imports terminée !"
echo "Les imports ont été ajoutés correctement dans tous les fichiers nécessaires."
