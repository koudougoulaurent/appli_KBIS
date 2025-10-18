"""
Formulaires sécurisés pour les utilisateurs
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, GroupeTravail
from core.security_validators import SecurityValidators


class SecureUtilisateurForm(forms.ModelForm):
    """Formulaire sécurisé pour créer/modifier un utilisateur"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe sécurisé',
            'minlength': '8',
            'maxlength': '128'
        }),
        required=False,
        help_text="Minimum 8 caractères avec majuscule, minuscule, chiffre et caractère spécial",
        validators=[SecurityValidators.validate_password_strength]
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le mot de passe'
        }),
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
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur unique',
                'minlength': '3',
                'maxlength': '30'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom',
                'maxlength': '50'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom',
                'maxlength': '50'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'adresse@email.com',
                'maxlength': '254'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+226 70 12 34 56',
                'maxlength': '20'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète',
                'maxlength': '500'
            }),
            'date_naissance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_embauche': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'groupe_travail': forms.Select(attrs={
                'class': 'form-select'
            }),
            'poste': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Poste occupé',
                'maxlength': '100'
            }),
            'departement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Département',
                'maxlength': '100'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser les labels et aide
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['username'].help_text = "3-30 caractères, lettres, chiffres, tirets et underscores"
        
        self.fields['first_name'].label = "Prénom"
        self.fields['first_name'].help_text = "Obligatoire, lettres uniquement"
        
        self.fields['last_name'].label = "Nom"
        self.fields['last_name'].help_text = "Obligatoire, lettres uniquement"
        
        self.fields['email'].label = "Adresse email"
        self.fields['email'].help_text = "Obligatoire et unique"
        
        self.fields['telephone'].label = "Téléphone"
        self.fields['telephone'].help_text = "Format international (ex: +226 70 12 34 56)"
        
        self.fields['groupe_travail'].label = "Groupe de travail"
        self.fields['groupe_travail'].help_text = "Sélectionnez le groupe de travail"
        self.fields['groupe_travail'].required = True
        
        # Rendre certains champs obligatoires
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
    
    def clean_username(self):
        """Valider le nom d'utilisateur"""
        username = self.cleaned_data.get('username')
        
        if username:
            # Validation de sécurité
            username = SecurityValidators.validate_username_security(username)
            
            # Vérifier l'unicité
            queryset = Utilisateur.objects.filter(username=username)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        
        return username
    
    def clean_first_name(self):
        """Valider le prénom"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            return SecurityValidators.validate_name_security(first_name)
        return first_name
    
    def clean_last_name(self):
        """Valider le nom"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            return SecurityValidators.validate_name_security(last_name)
        return last_name
    
    def clean_email(self):
        """Valider l'email avec sécurité"""
        email = self.cleaned_data.get('email')
        
        if email:
            # Validation de sécurité
            email = SecurityValidators.validate_email_security(email)
            
            # Vérifier l'unicité
            queryset = Utilisateur.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Cette adresse email est déjà utilisée.")
        
        return email
    
    def clean_telephone(self):
        """Valider le téléphone avec sécurité"""
        telephone = self.cleaned_data.get('telephone')
        
        if telephone:
            # Validation de sécurité
            telephone = SecurityValidators.validate_phone_international(telephone)
            
            # Vérifier l'unicité
            queryset = Utilisateur.objects.filter(telephone=telephone)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        
        return telephone
    
    def clean_password(self):
        """Valider le mot de passe"""
        password = self.cleaned_data.get('password')
        
        if password:
            return SecurityValidators.validate_password_strength(password)
        
        return password
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        # Validation du mot de passe
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation des champs obligatoires
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not cleaned_data.get(field):
                raise ValidationError(f"Le champ {self.fields[field].label} est obligatoire.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sauvegarder l'utilisateur avec sécurité"""
        user = super().save(commit=False)
        
        # Gérer le mot de passe
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        
        return user


class SecureGroupeTravailForm(forms.ModelForm):
    """Formulaire sécurisé pour les groupes de travail"""
    
    class Meta:
        model = GroupeTravail
        fields = ['nom', 'description', 'permissions', 'actif']
        widgets = {
            'nom': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': '500'
            }),
            'permissions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'maxlength': '2000'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['nom'].label = "Nom du groupe"
        self.fields['nom'].help_text = "Sélectionnez le nom du groupe de travail"
        
        self.fields['description'].label = "Description"
        self.fields['description'].help_text = "Description du groupe (max 500 caractères)"
        
        self.fields['permissions'].label = "Permissions"
        self.fields['permissions'].help_text = """
        Permissions au format JSON (max 2000 caractères). Exemple:
        {
            "modules": ["paiements", "retraits", "proprietes"],
            "actions": ["read", "write", "delete"]
        }
        """
    
    def clean_description(self):
        """Valider la description"""
        description = self.cleaned_data.get('description')
        
        if description and len(description) > 500:
            raise ValidationError("La description ne peut pas dépasser 500 caractères.")
        
        return description
    
    def clean_permissions(self):
        """Valider les permissions JSON"""
        permissions = self.cleaned_data.get('permissions')
        
        if permissions:
            if len(permissions) > 2000:
                raise ValidationError("Les permissions ne peuvent pas dépasser 2000 caractères.")
            
            try:
                import json
                if isinstance(permissions, str):
                    json.loads(permissions)
                return permissions
            except json.JSONDecodeError:
                raise ValidationError("Le format JSON n'est pas valide.")
        
        return permissions


class SecureConnexionForm(forms.Form):
    """Formulaire de connexion sécurisé"""
    
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nom d\'utilisateur',
            'autocomplete': 'username'
        }),
        label="Nom d'utilisateur",
        validators=[SecurityValidators.validate_username_security]
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Mot de passe',
            'autocomplete': 'current-password'
        }),
        label="Mot de passe"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].help_text = "Entrez votre nom d'utilisateur"
        self.fields['password'].help_text = "Entrez votre mot de passe"
