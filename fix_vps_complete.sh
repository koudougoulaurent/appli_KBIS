#!/bin/bash

# Script complet pour corriger tous les problemes sur le VPS
echo "Correction complete des problemes sur le VPS..."

cd /var/www/kbis_immobilier

# 1. Corriger les references RecapitulatifMensuelBailleur
echo "1. Correction des references RecapitulatifMensuelBailleur..."

files=(
    "paiements/views_recus.py"
    "paiements/views_kbis_recus.py"
    "paiements/forms.py"
    "paiements/services_recus.py"
    "paiements/views_charges_avancees.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Correction de $file..."
        cp "$file" "$file.backup"
        sed -i 's/RecapitulatifMensuelBailleur/RecapMensuel/g' "$file"
        echo "  OK: $file corrige"
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

# 2. Corriger les imports manquants
echo "2. Correction des imports manquants..."

# Corriger views_recus.py
if [ -f "paiements/views_recus.py" ]; then
    echo "Correction des imports dans views_recus.py..."
    sed -i 's/# from .models import RecuRecapitulatif, RecapMensuel  # Modeles supprimes/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecuRecapitulatif, RecapMensuel/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecapMensuel$/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    echo "  OK: views_recus.py corrige"
fi

# Corriger views_charges_avancees.py
if [ -f "paiements/views_charges_avancees.py" ]; then
    echo "Correction des imports dans views_charges_avancees.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_charges_avancees.py"
    echo "  OK: views_charges_avancees.py corrige"
fi

# Corriger views_kbis_recus.py
if [ -f "paiements/views_kbis_recus.py" ]; then
    echo "Correction des imports dans views_kbis_recus.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_kbis_recus.py"
    echo "  OK: views_kbis_recus.py corrige"
fi

# 3. Ajouter le modele RecuRecapitulatif si necessaire
echo "3. Verification du modele RecuRecapitulatif..."

if ! grep -q "class RecuRecapitulatif" "paiements/models.py"; then
    echo "Ajout du modele RecuRecapitulatif..."
    
    # Ajouter le modele a la fin du fichier
    cat >> "paiements/models.py" << 'EOF'

class RecuRecapitulatif(models.Model):
    """Modele pour les recus de recapitulatifs mensuels - PROFESSIONNEL."""
    
    # Numero unique du recu
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numero de recu"),
        help_text=_("Numero unique du recu de recapitulatif")
    )
    
    # Recapitulatif associe
    recapitulatif = models.OneToOneField(
        RecapMensuel,
        on_delete=models.CASCADE,
        related_name='recu',
        verbose_name=_("Recapitulatif")
    )
    
    # Type de recu
    type_recu = models.CharField(
        max_length=20,
        choices=[
            ('recapitulatif', 'Recapitulatif'),
            ('quittance', 'Quittance'),
            ('attestation', 'Attestation'),
            ('releve', 'Releve'),
            ('facture', 'Facture'),
        ],
        default='recapitulatif',
        verbose_name=_("Type de recu")
    )
    
    # Template utilise
    template_utilise = models.CharField(
        max_length=20,
        choices=[
            ('professionnel', 'Professionnel'),
            ('entreprise', 'Entreprise'),
            ('luxe', 'Luxe'),
            ('standard', 'Standard'),
            ('gestimmob', 'GESTIMMOB'),
        ],
        default='professionnel',
        verbose_name=_("Template utilise")
    )
    
    # Format d'impression
    format_impression = models.CharField(
        max_length=20,
        choices=[
            ('A4_paysage', 'A4 Paysage'),
            ('A4_portrait', 'A4 Portrait'),
            ('A3_paysage', 'A3 Paysage'),
            ('lettre_paysage', 'Lettre Paysage'),
        ],
        default='A4_paysage',
        verbose_name=_("Format d'impression")
    )
    
    # Statut du recu
    statut = models.CharField(
        max_length=20,
        choices=[
            ('brouillon', 'Brouillon'),
            ('valide', 'Valide'),
            ('imprime', 'Imprime'),
            ('envoye', 'Envoye'),
            ('archive', 'Archive'),
        ],
        default='brouillon',
        verbose_name=_("Statut du recu")
    )
    
    # Informations d'impression
    imprime = models.BooleanField(
        default=False,
        verbose_name=_("Recu imprime")
    )
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    imprime_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_recapitulatifs_imprimes',
        verbose_name=_("Imprime par")
    )
    nombre_impressions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre d'impressions")
    )
    
    # Informations d'envoi
    envoye = models.BooleanField(
        default=False,
        verbose_name=_("Recu envoye")
    )
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi")
    )
    mode_envoi = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('courrier', 'Courrier'),
            ('remise_main', 'Remise en main propre'),
            ('fax', 'Fax'),
        ],
        blank=True,
        verbose_name=_("Mode d'envoi")
    )
    
    # Metadonnees
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de creation")
    )
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_recapitulatifs_crees',
        verbose_name=_("Cree par")
    )
    
    # Hash de securite
    hash_securite = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Hash de securite")
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Recu de recapitulatif")
        verbose_name_plural = _("Recus de recapitulatifs")
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero_recu']),
            models.Index(fields=['statut', 'date_creation']),
            models.Index(fields=['recapitulatif', 'type_recu']),
        ]
    
    def __str__(self):
        return f"Recu {self.numero_recu} - {self.recapitulatif.bailleur.get_nom_complet()}"
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            self.numero_recu = self.generer_numero_recu()
        super().save(*args, **kwargs)
    
    def generer_numero_recu(self):
        """Genere un numero de recu unique."""
        from datetime import datetime
        import random
        
        # Format: REC-YYYYMMDD-XXXX
        date_str = datetime.now().strftime('%Y%m%d')
        random_num = random.randint(1000, 9999)
        numero = f"REC-{date_str}-{random_num}"
        
        # Verifier l'unicite
        while RecuRecapitulatif.objects.filter(numero_recu=numero).exists():
            random_num = random.randint(1000, 9999)
            numero = f"REC-{date_str}-{random_num}"
        
        return numero
    
    def marquer_imprime(self, utilisateur):
        """Marque le recu comme imprime."""
        from django.utils import timezone
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.nombre_impressions += 1
        self.statut = 'imprime'
        self.save()
    
    def marquer_envoye(self, mode_envoi):
        """Marque le recu comme envoye."""
        from django.utils import timezone
        self.envoye = True
        self.date_envoi = timezone.now()
        self.mode_envoi = mode_envoi
        self.statut = 'envoye'
        self.save()
    
    def generer_hash_securite(self):
        """Genere un hash de securite pour le recu."""
        import hashlib
        
        data = f"{self.numero_recu}{self.recapitulatif.pk}{self.date_creation.isoformat()}"
        self.hash_securite = hashlib.sha256(data.encode()).hexdigest()
        self.save()
    
    def get_absolute_url(self):
        return reverse('paiements:detail_recu_recapitulatif', kwargs={'pk': self.pk})
EOF
    
    echo "  OK: Modele RecuRecapitulatif ajoute"
else
    echo "  OK: Modele RecuRecapitulatif deja present"
fi

echo "Correction terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction complete terminee avec succes!"
