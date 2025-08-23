from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, GroupeTravail

class UtilisateurForm(forms.ModelForm):
    """Formulaire pour créer/modifier un utilisateur"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Laissez vide pour conserver le mot de passe actuel"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Confirmez le mot de passe"
    )
    
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'telephone', 'adresse', 'date_naissance', 'photo',
            'groupe_travail', 'poste', 'departement', 'date_embauche',
            'actif', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser les champs
        self.fields['username'].help_text = "Nom d'utilisateur unique pour la connexion"
        self.fields['email'].required = True
        self.fields['groupe_travail'].required = True
        self.fields['groupe_travail'].label = "Groupe de travail"
        self.fields['groupe_travail'].help_text = "Sélectionnez le groupe de travail (CAISSE, CONTROLES, PAIEMENT, PRIVILEGE)"
        
        # Personnaliser les labels
        self.fields['first_name'].label = "Prénom"
        self.fields['last_name'].label = "Nom"
        self.fields['telephone'].label = "Téléphone"
        self.fields['adresse'].label = "Adresse"
        self.fields['date_naissance'].label = "Date de naissance"
        self.fields['photo'].label = "Photo de profil"
        self.fields['poste'].label = "Poste"
        self.fields['departement'].label = "Département"
        self.fields['date_embauche'].label = "Date d'embauche"
        self.fields['actif'].label = "Utilisateur actif"
        self.fields['is_staff'].label = "Accès staff"
        self.fields['is_superuser'].label = "Super utilisateur"
        
        # Ajouter des classes Bootstrap
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Gérer le mot de passe
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        
        return user

class GroupeTravailForm(forms.ModelForm):
    """Formulaire pour créer/modifier un groupe de travail"""
    
    class Meta:
        model = GroupeTravail
        fields = ['nom', 'description', 'permissions', 'actif']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'permissions': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser les champs
        self.fields['nom'].widget.attrs.update({'class': 'form-control'})
        self.fields['actif'].widget.attrs.update({'class': 'form-check-input'})
        
        # Aide pour le champ permissions
        self.fields['permissions'].help_text = """
        Entrez les permissions au format JSON. Exemple:
        {
            "modules": ["paiements", "retraits", "proprietes"],
            "actions": ["read", "write", "delete"]
        }
        """
    
    def clean_permissions(self):
        permissions = self.cleaned_data.get('permissions')
        
        if permissions:
            try:
                # Vérifier que c'est du JSON valide
                import json
                if isinstance(permissions, str):
                    json.loads(permissions)
                return permissions
            except json.JSONDecodeError:
                raise forms.ValidationError("Le format JSON n'est pas valide.")
        
        return permissions

class ConnexionGroupeForm(forms.Form):
    """Formulaire pour la sélection du groupe de travail"""
    
    groupe = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label="CHOIX DU GROUPE DE TRAVAIL :"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer les groupes actifs
        groupes_actifs = GroupeTravail.objects.filter(actif=True).order_by('nom')
        self.fields['groupe'].choices = [('', 'Sélectionnez un groupe...')] + [
            (groupe.nom, groupe.nom) for groupe in groupes_actifs
        ]

class LoginGroupeForm(forms.Form):
    """Formulaire de connexion pour un groupe spécifique"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nom d\'utilisateur'
        }),
        label="Nom d'utilisateur"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Mot de passe'
        }),
        label="Mot de passe"
    )
    
    def __init__(self, groupe_nom=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groupe_nom = groupe_nom
        
        if groupe_nom:
            self.fields['username'].help_text = f"Entrez vos identifiants pour le groupe {groupe_nom}" 