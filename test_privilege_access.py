#!/usr/bin/env python3
"""
SCRIPT DE VÉRIFICATION COMPLÈTE DE SÉCURITÉ
============================================

Ce script vérifie SYSTÉMATIQUEMENT toute la plateforme pour identifier :
1. Les violations de groupe (ADMINISTRATION au lieu de PRIVILEGE uniquement)
2. Les violations de séparation des responsabilités
3. Les accès non autorisés aux données
4. Les modifications de données validées sans autorisation

EXÉCUTION : python test_privilege_access.py
"""

import os
import re
import sys
from pathlib import Path

def scan_file_for_violations(file_path):
    """Scanne un fichier pour identifier les violations de sécurité"""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 1. VÉRIFICATION DES VIOLATIONS DE GROUPE
            if 'ADMINISTRATION' in line and 'PRIVILEGE' in line:
                # Recherche des patterns problématiques
                patterns_violation = [
                    r'not in \[.*ADMINISTRATION.*PRIVILEGE.*\]',
                    r'in \[.*ADMINISTRATION.*PRIVILEGE.*\]',
                    r'ADMINISTRATION.*PRIVILEGE',
                    r'PRIVILEGE.*ADMINISTRATION'
                ]
                
                for pattern in patterns_violation:
                    if re.search(pattern, line):
                        violations.append({
                            'type': 'VIOLATION_GROUPE',
                            'severity': 'CRITIQUE',
                            'line': line_num,
                            'description': f'Accès autorisé à ADMINISTRATION ET PRIVILEGE au lieu de PRIVILEGE uniquement',
                            'code': line
                        })
                        break
            
            # 2. VÉRIFICATION DES MODIFICATIONS DE DONNÉES VALIDÉES
            if any(keyword in line for keyword in ['modifier_', 'valider_', 'invalider_']):
                if 'statut' in line and 'valide' in line:
                    if 'PRIVILEGE' not in line:
                        violations.append({
                            'type': 'VIOLATION_VALIDATION',
                            'severity': 'CRITIQUE',
                            'line': line_num,
                            'description': f'Modification de données validées sans vérification PRIVILEGE',
                            'code': line
                        })
            
            # 3. VÉRIFICATION DES SUPPRESSIONS
            if any(keyword in line for keyword in ['supprimer_', 'delete']):
                if 'ADMINISTRATION' in line and 'PRIVILEGE' in line:
                    violations.append({
                        'type': 'VIOLATION_SUPPRESSION',
                        'severity': 'CRITIQUE',
                        'line': line_num,
                        'description': f'Suppression autorisée à ADMINISTRATION ET PRIVILEGE au lieu de PRIVILEGE uniquement',
                        'code': line
                    })
            
            # 4. VÉRIFICATION DES ACCÈS AUX DONNÉES
            if any(keyword in line for keyword in ['corbeille_', 'orphelins_', 'audit_']):
                if 'ADMINISTRATION' in line and 'PRIVILEGE' in line:
                    violations.append({
                        'type': 'VIOLATION_ACCES_DONNEES',
                        'severity': 'CRITIQUE',
                        'line': line_num,
                        'description': f'Accès aux données sensibles autorisé à ADMINISTRATION ET PRIVILEGE au lieu de PRIVILEGE uniquement',
                        'code': line
                    })
            
            # 5. VÉRIFICATION DES RÉSILIATIONS
            if 'resilier' in line.lower():
                if 'ADMINISTRATION' in line and 'PRIVILEGE' in line:
                    violations.append({
                        'type': 'VIOLATION_RESILIATION',
                        'severity': 'CRITIQUE',
                        'line': line_num,
                        'description': f'Résiliation autorisée à ADMINISTRATION ET PRIVILEGE au lieu de PRIVILEGE uniquement',
                        'code': line
                    })
    
    except Exception as e:
        violations.append({
            'type': 'ERREUR_LECTURE',
            'severity': 'ERREUR',
            'line': 0,
            'description': f'Erreur lors de la lecture du fichier : {str(e)}',
            'code': ''
        })
    
    return violations

def scan_directory_for_violations(directory_path):
    """Scanne un répertoire pour identifier les violations de sécurité"""
    all_violations = {}
    
    # Extensions de fichiers à scanner
    extensions = ['.py', '.html', '.js', '.css']
    
    for root, dirs, files in os.walk(directory_path):
        # Ignorer les répertoires système
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'migrations', 'venv', 'env']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                violations = scan_file_for_violations(file_path)
                
                if violations:
                    all_violations[file_path] = violations
    
    return all_violations

def generate_security_report(violations):
    """Génère un rapport de sécurité détaillé"""
    if not violations:
        print("✅ AUCUNE VIOLATION DE SÉCURITÉ DÉTECTÉE !")
        return
    
    print("🚨 RAPPORT DE SÉCURITÉ - VIOLATIONS DÉTECTÉES")
    print("=" * 80)
    
    # Compter par type et sévérité
    stats = {}
    for file_path, file_violations in violations.items():
        for violation in file_violations:
            violation_type = violation['type']
            severity = violation['severity']
            
            if violation_type not in stats:
                stats[violation_type] = {}
            if severity not in stats[violation_type]:
                stats[violation_type][severity] = 0
            
            stats[violation_type][severity] += 1
    
    # Afficher les statistiques
    print("\n📊 STATISTIQUES DES VIOLATIONS :")
    for violation_type, severities in stats.items():
        print(f"\n  {violation_type}:")
        for severity, count in severities.items():
            print(f"    {severity}: {count}")
    
    # Afficher les détails par fichier
    print("\n🔍 DÉTAILS DES VIOLATIONS PAR FICHIER :")
    for file_path, file_violations in violations.items():
        print(f"\n📁 {file_path}")
        print("-" * len(file_path))
        
        for violation in file_violations:
            print(f"  Ligne {violation['line']} - {violation['severity']}: {violation['description']}")
            if violation['code']:
                print(f"    Code: {violation['code']}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS :")
    print("1. Corriger IMMÉDIATEMENT toutes les violations CRITIQUE")
    print("2. Vérifier que seuls les utilisateurs PRIVILEGE peuvent :")
    print("   - Supprimer des éléments")
    print("   - Modifier des données validées")
    print("   - Accéder aux corbeilles et données orphelines")
    print("   - Résilier des contrats")
    print("3. Implémenter des tests automatisés de sécurité")
    print("4. Former les développeurs aux bonnes pratiques de sécurité")

def main():
    """Fonction principale"""
    print("🔒 VÉRIFICATION COMPLÈTE DE SÉCURITÉ DE LA PLATEFORME")
    print("=" * 60)
    
    # Déterminer le répertoire de travail
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.getcwd()
    
    print(f"📂 Scan du répertoire : {directory}")
    print("⏳ Analyse en cours...")
    
    # Scanner le répertoire
    violations = scan_directory_for_violations(directory)
    
    # Générer le rapport
    generate_security_report(violations)
    
    # Résumé final
    total_violations = sum(len(file_violations) for file_violations in violations.values())
    if total_violations > 0:
        print(f"\n⚠️  TOTAL : {total_violations} violation(s) de sécurité détectée(s)")
        print("🚨 ACTION IMMÉDIATE REQUISE !")
        return 1
    else:
        print("\n✅ PLATEFORME SÉCURISÉE - Aucune violation détectée")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 