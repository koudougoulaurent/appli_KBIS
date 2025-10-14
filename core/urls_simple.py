from django.urls import path
from django.http import HttpResponse

def simple_home(request):
    """Page d'accueil ultra-simple"""
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Application KBIS - Déployée avec succès !</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .success { background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .info { background: #d1ecf1; color: #0c5460; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; margin-top: 40px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Application KBIS Déployée avec Succès !</h1>
            
            <div class="success">
                <h2>✅ Déploiement Réussi</h2>
                <p>Votre application Django est maintenant en ligne sur Render !</p>
                <p><strong>URL :</strong> https://appli-kbis.onrender.com</p>
            </div>
            
            <div class="info">
                <h2>📋 Informations</h2>
                <p>Cette version simplifiée fonctionne sans base de données pour assurer un déploiement rapide.</p>
                <p>Les fonctionnalités complètes seront ajoutées progressivement.</p>
            </div>
            
            <div class="footer">
                <p>Déployé le 14 octobre 2025 | Powered by Django & Render</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

app_name = 'core'

urlpatterns = [
    path('', simple_home, name='home'),
]
