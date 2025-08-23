#!/usr/bin/env python
"""
Script de test qui utilise le serveur Django réel
"""
import requests
import json

def test_dashboard_serveur():
    """Test des dashboards via le serveur Django"""
    print("🔍 Test des dashboards via le serveur Django")
    print("-" * 40)
    
    base_url = "http://127.0.0.1:8000"
    
    # Configuration des tests
    tests = [
        ('CAISSE', 'test_caisse', 'test123'),
        ('ADMINISTRATION', 'test_administration', 'test123'),
        ('CONTROLES', 'test_controles', 'test123'),
        ('PRIVILEGE', 'test_privilege', 'test123'),
    ]
    
    session = requests.Session()
    
    for groupe_nom, username, password in tests:
        print(f"\n🔍 Test du dashboard {groupe_nom}")
        print("-" * 30)
        
        try:
            # 1. Se connecter au groupe
            login_url = f"{base_url}/utilisateurs/login/{groupe_nom}/"
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': 'dummy'  # Django gère automatiquement
            }
            
            response = session.post(login_url, data=login_data, allow_redirects=False)
            
            if response.status_code == 302:  # Redirection après connexion
                print(f"✅ Connexion réussie pour {username}")
                
                # 2. Accéder au dashboard
                dashboard_url = f"{base_url}/utilisateurs/dashboard/{groupe_nom}/"
                response = session.get(dashboard_url)
                
                if response.status_code == 200:
                    print(f"✅ Dashboard {groupe_nom} accessible")
                    
                    # Vérifier le contenu de la page
                    content = response.text
                    
                    # Vérifier la présence des statistiques dans le HTML
                    if 'paiements_mois' in content or 'total_proprietes' in content or 'total_utilisateurs' in content:
                        print(f"✅ Statistiques présentes dans le HTML")
                        
                        # Extraire quelques statistiques du HTML
                        if 'paiements_mois' in content:
                            print(f"   - Statistiques CAISSE détectées")
                        if 'total_proprietes' in content:
                            print(f"   - Statistiques ADMINISTRATION détectées")
                        if 'total_utilisateurs' in content:
                            print(f"   - Statistiques PRIVILEGE détectées")
                        if 'paiements_a_valider' in content:
                            print(f"   - Statistiques CONTROLES détectées")
                    else:
                        print(f"❌ Aucune statistique détectée dans le HTML")
                        
                else:
                    print(f"❌ Erreur {response.status_code} pour le dashboard {groupe_nom}")
                    
            else:
                print(f"❌ Échec de la connexion pour {username}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Impossible de se connecter au serveur Django")
            print(f"   Assurez-vous que le serveur tourne sur http://127.0.0.1:8000")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION DES DASHBOARDS VIA SERVEUR DJANGO")
    print("=" * 60)
    
    test_dashboard_serveur()
    
    print("\n" + "=" * 60)
    print("📋 INSTRUCTIONS")
    print("=" * 60)
    print("1. Assurez-vous que le serveur Django tourne:")
    print("   python manage.py runserver 127.0.0.1:8000")
    print("\n2. Accédez aux dashboards via votre navigateur:")
    print("   - CAISSE: http://127.0.0.1:8000/utilisateurs/login/CAISSE/")
    print("   - ADMINISTRATION: http://127.0.0.1:8000/utilisateurs/login/ADMINISTRATION/")
    print("   - CONTROLES: http://127.0.0.1:8000/utilisateurs/login/CONTROLES/")
    print("   - PRIVILEGE: http://127.0.0.1:8000/utilisateurs/login/PRIVILEGE/")
    print("\n3. Identifiants de test:")
    print("   - CAISSE: test_caisse / test123")
    print("   - ADMINISTRATION: test_administration / test123")
    print("   - CONTROLES: test_controles / test123")
    print("   - PRIVILEGE: test_privilege / test123")

if __name__ == '__main__':
    main() 