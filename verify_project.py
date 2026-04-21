#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(command, description):
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        print(f"✅ {description} réussi.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} échoué.")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    success = True
    
    # 1. Run all tests
    if not run_command("pytest tests/", "Exécution de tous les tests (pytest)"):
        success = False
        
    if success:
        print("\n✨ PROJET VALIDE : Aucune régression détectée.")
    else:
        print("\n⚠️ DES ERREURS ONT ÉTÉ DÉTECTÉES.")
        sys.exit(1)

if __name__ == "__main__":
    main()
