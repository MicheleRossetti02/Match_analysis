#!/usr/bin/env python3
"""
Interactive Setup Script for Football Prediction System
Guides user through API key configuration and initial data collection
"""
import os
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_step(number, text):
    """Print formatted step"""
    print(f"\n{'='*70}")
    print(f"📍 STEP {number}: {text}")
    print(f"{'='*70}\n")


def check_env_file():
    """Check if .env file exists"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if env_path.exists():
        print("✅ File .env trovato!")
        return True
    elif env_example_path.exists():
        print("⚠️  File .env non trovato, ma .env.example esiste.")
        create = input("Vuoi creare .env da .env.example? (s/n): ").lower()
        if create == 's':
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ File .env creato!")
            return True
    else:
        print("❌ Né .env né .env.example trovati!")
        return False
    
    return False


def configure_api_key():
    """Interactive API key configuration"""
    print_step(1, "Configurazione API Key")
    
    print("📋 Per ottenere la tua API key:\n")
    print("1. Vai su: https://rapidapi.com/api-sports/api/api-football")
    print("2. Clicca 'Sign Up' e crea un account (gratis)")
    print("3. Clicca 'Subscribe to Test' per il piano gratuito")
    print("4. Copia la tua 'X-RapidAPI-Key'\n")
    
    input("Premi INVIO quando hai ottenuto la tua API key...")
    
    api_key = input("\n🔑 Incolla qui la tua API key: ").strip()
    
    if not api_key:
        print("❌ API key vuota! Riprova.")
        return False
    
    # Update .env file
    env_path = Path('.env')
    
    try:
        # Read current .env
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update API_FOOTBALL_KEY
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('API_FOOTBALL_KEY='):
                    lines[i] = f'API_FOOTBALL_KEY={api_key}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'\nAPI_FOOTBALL_KEY={api_key}\n')
            
            # Write back
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            print("\n✅ API key configurata con successo!")
            return True
        else:
            print("❌ File .env non trovato!")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante la configurazione: {e}")
        return False


def test_api_connection():
    """Test API connection"""
    print_step(2, "Test Connessione API")
    
    print("🔍 Sto testando la connessione con API-Football...\n")
    
    try:
        sys.path.append('src')
        from data_collection.api_client import APIFootballClient
        
        client = APIFootballClient()
        
        # Try to fetch leagues
        print("Tentativo di fetch delle leghe...")
        leagues = client.get_leagues(season=2024)
        
        if leagues:
            print(f"\n✅ Connessione riuscita!")
            print(f"✅ Trovate {len(leagues)} leghe")
            print("\nLeghe disponibili:")
            for league in leagues[:5]:
                league_data = league.get('league', {})
                country_data = league.get('country', {})
                print(f"   - {league_data.get('name')} ({country_data.get('name')})")
            
            client.close()
            return True
        else:
            print("⚠️  Nessuna lega trovata. Verifica la tua API key.")
            client.close()
            return False
            
    except Exception as e:
        print(f"\n❌ Errore durante il test: {e}")
        print("\nPossibili cause:")
        print("- API key non valida")
        print("- Problemi di connessione internet")
        print("- API temporaneamente non disponibile")
        return False


def initialize_database():
    """Initialize database"""
    print_step(3, "Inizializzazione Database")
    
    print("🗄️  Creazione tabelle database...\n")
    
    try:
        sys.path.append('src')
        from models.database import init_db
        
        init_db()
        print("✅ Database inizializzato con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione: {e}")
        print("\nAssicurati che PostgreSQL sia in esecuzione:")
        print("  docker-compose up -d postgres")
        return False


def collect_initial_data():
    """Run initial data collection"""
    print_step(4, "Raccolta Dati Iniziale")
    
    print("📊 Modalità raccolta dati:\n")
    print("1. 🚀 Quick (ultimi 30 giorni) - Consigliato per iniziare")
    print("2. 📅 Standard (ultimi 6 mesi)")
    print("3. 📈 Completo (ultimi 12 mesi)")
    
    choice = input("\nScegli modalità (1/2/3): ").strip()
    
    months_map = {
        '1': 1,
        '2': 6,
        '3': 12
    }
    
    months = months_map.get(choice, 1)
    
    print(f"\n🎯 Avvio raccolta dati (ultimi {months} {'mese' if months == 1 else 'mesi'})...")
    print("\n⏱️  Questo potrebbe richiedere alcuni minuti...")
    print("💡 Vedrai il progresso in tempo reale\n")
    
    input("Premi INVIO per iniziare...")
    
    try:
        sys.path.append('src')
        from data_collection.data_collector import DataCollector
        
        collector = DataCollector()
        
        collector.collect_historical_data(
            season=2024,
            months_back=months,
            include_statistics=False  # Start without stats to save API calls
        )
        
        collector.close()
        
        print("\n" + "="*70)
        print("🎉 RACCOLTA DATI COMPLETATA!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Errore durante la raccolta: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_collected_data():
    """Verify collected data"""
    print_step(5, "Verifica Dati Raccolti")
    
    print("🔍 Verifica dati nel database...\n")
    
    try:
        sys.path.append('src')
        from models.database import SessionLocal, League, Team, Match
        
        db = SessionLocal()
        
        leagues_count = db.query(League).count()
        teams_count = db.query(Team).count()
        matches_count = db.query(Match).count()
        
        print(f"✅ Leghe: {leagues_count}")
        print(f"✅ Squadre: {teams_count}")
        print(f"✅ Partite: {matches_count}")
        
        if matches_count > 0:
            print("\n🎯 Dati raccolti con successo!")
            print("\nPuoi ora:")
            print("1. Avviare il backend: python src/api/main.py")
            print("2. Avviare il frontend: cd ../frontend && npm run dev")
            print("3. Visualizzare i dati su: http://localhost:5173")
        else:
            print("\n⚠️  Nessuna partita raccolta. Potrebbe essere necessario:")
            print("- Verificare l'intervallo di date")
            print("- Eseguire nuovamente la raccolta")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        return False


def main():
    """Main setup function"""
    print_header("🚀 SETUP FOOTBALL PREDICTION SYSTEM")
    
    print("Benvenuto! Questo script ti guiderà attraverso:")
    print("1. ✅ Configurazione API key")
    print("2. ✅ Test connessione")
    print("3. ✅ Inizializzazione database")
    print("4. ✅ Raccolta dati iniziale")
    print("5. ✅ Verifica risultati")
    
    input("\nPremi INVIO per iniziare...")
    
    # Check we're in the right directory
    if not Path('src').exists():
        print("\n❌ Errore: Esegui questo script dalla directory backend/")
        print("   cd backend")
        print("   python setup_interactive.py")
        return
    
    # Step 1: Configure API key
    if not check_env_file():
        print("❌ Setup interrotto. Crea prima il file .env.")
        return
    
    if not configure_api_key():
        print("❌ Setup interrotto.")
        return
    
    # Step 2: Test API
    if not test_api_connection():
        retry = input("\n⚠️  Test fallito. Vuoi riprovare? (s/n): ").lower()
        if retry == 's':
            if not configure_api_key():
                return
            if not test_api_connection():
                print("❌ Setup interrotto.")
                return
        else:
            print("❌ Setup interrotto.")
            return
    
    # Step 3: Initialize database
    if not initialize_database():
        print("\n⚠️  Errore database. Assicurati che PostgreSQL sia in esecuzione.")
        print("   Prova: docker-compose up -d postgres")
        return
    
    # Step 4: Collect data
    if not collect_initial_data():
        print("⚠️  Raccolta dati non completata.")
        return
    
    # Step 5: Verify
    verify_collected_data()
    
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETATO CON SUCCESSO!")
    print("="*70)
    print("\n📚 Prossimi passi:")
    print("\n1. Avvia il backend:")
    print("   python src/api/main.py")
    print("\n2. In un altro terminale, avvia il frontend:")
    print("   cd ../frontend")
    print("   npm install  # se non già fatto")
    print("   npm run dev")
    print("\n3. Apri il browser su: http://localhost:5173")
    print("\n4. Documentazione: Vedi README.md e DATA_COLLECTION.md")
    print("\n✨ Buon divertimento!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrotto dall'utente.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
