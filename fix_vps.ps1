# Script PowerShell pour corriger le VPS
Write-Host "=== Correction automatisée du VPS ===" -ForegroundColor Green

# 1. Sauvegarder le fichier models.py sur le VPS
Write-Host "1. Sauvegarde du fichier models.py..." -ForegroundColor Yellow
$backupCmd = "cd /var/www/kbis_immobilier && cp paiements/models.py paiements/models.py.backup_$(date +%Y%m%d_%H%M%S)"
ssh root@78.138.58.185 $backupCmd

# 2. Copier le fichier models.py complet
Write-Host "2. Copie du fichier models.py..." -ForegroundColor Yellow
scp paiements/models.py root@78.138.58.185:/var/www/kbis_immobilier/paiements/models.py

# 3. Corriger le fichier views_recus.py
Write-Host "3. Correction du fichier views_recus.py..." -ForegroundColor Yellow
$fixCmd = @"
cd /var/www/kbis_immobilier
# Nettoyer les marqueurs Git
sed -i '/<<<<<<< Updated upstream/d; /=======/d; />>>>>>> Stashed changes/d' paiements/views_recus.py
# Vérifier la syntaxe
python3 -m py_compile paiements/views_recus.py
"@
ssh root@78.138.58.185 $fixCmd

# 4. Vérifier Django et redémarrer
Write-Host "4. Vérification Django et redémarrage..." -ForegroundColor Yellow
$restartCmd = @"
cd /var/www/kbis_immobilier
source venv/bin/activate
python manage.py check
python manage.py makemigrations
python manage.py migrate
sudo systemctl restart gunicorn
sudo systemctl restart nginx
"@
ssh root@78.138.58.185 $restartCmd

Write-Host "=== Correction terminée ===" -ForegroundColor Green
Write-Host "Testez maintenant: https://78.138.58.185/paiements/recus-recapitulatifs/creer/1/" -ForegroundColor Cyan
