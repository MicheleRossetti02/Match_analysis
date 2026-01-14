# 🚀 Guida Rapida - Configurazione e Raccolta Dati

Guida passo-passo per configurare l'API key e raccogliere i dati.

---

## 📋 Metodo 1: Script Interattivo (Consigliato)

Lo script interattivo ti guida attraverso tutti i passaggi automaticamente.

### Passaggi:

```bash
cd backend

# Attiva l'ambiente virtuale
source venv/bin/activate  # Su Windows: venv\Scripts\activate

# Esegui lo script interattivo
python setup_interactive.py
```

Lo script ti chiederà:
1. ✅ Di incollare la tua API key
2. ✅ Testerà la connessione
3. ✅ Inizializzerà il database
4. ✅ Raccoglierà i dati (scegli quick/standard/completo)
5. ✅ Verificherà i risultati

---

## 📋 Metodo 2: Configurazione Manuale

### Passo 1: Ottenere API Key

1. Vai su **[RapidAPI - API-Football](https://rapidapi.com/api-sports/api/api-football)**

2. Clicca **"Sign Up"** in alto a destra
   - Puoi registrarti con email, Google, o GitHub

3. Dopo il login, cerca **"API-Football"**

4. Clicca **"Subscribe to Test"** (piano gratuito)
   - 100 richieste al giorno gratuitamente
   - Nessuna carta di credito richiesta per il piano free

5. Nella pagina dell'API, troverai le tue credenziali:
   ```
   X-RapidAPI-Key: la_tua_chiave_qui
   X-RapidAPI-Host: api-football-v1.p.rapidapi.com
   ```

6. **Copia la chiave** (quella lunga tipo `abc123def456...`)

---

### Passo 2: Configurare .env

1. Vai nella cartella backend:
   ```bash
   cd backend
   ```

2. Crea il file `.env` da `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Apri `.env` con un editor di testo:
   ```bash
   nano .env
   # oppure usa VSCode, TextEdit, etc.
   ```

4. Trova la riga:
   ```env
   API_FOOTBALL_KEY=your_api_key_here
   ```

5. Sostituisci `your_api_key_here` con la tua chiave:
   ```env
   API_FOOTBALL_KEY=abc123def456ghi789...
   ```

6. Salva il file

---

### Passo 3: Testare la Connessione

```bash
# Attiva virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Testa l'API
python src/data_collection/api_client.py
```

**Output atteso:**
```
🔍 Testing API Football Client...

📊 Found 5 leagues
⚽ Found 20 teams in Premier League
📅 Found X upcoming matches

✅ Test completed!
```

Se vedi errori:
- ❌ `401 Unauthorized` → API key errata o non configurata
- ❌ `429 Too Many Requests` → Hai esaurito le 100 richieste giornaliere
- ❌ `403 Forbidden` → Sottoscrizione non attiva

---

### Passo 4: Inizializzare Database

**Opzione A: Docker (Consigliato)**
```bash
# Torna alla root del progetto
cd ..

# Avvia PostgreSQL
docker-compose up -d postgres

# Torna al backend
cd backend
```

**Opzione B: PostgreSQL Locale**
- Assicurati che PostgreSQL sia installato e in esecuzione
- Verifica la connessione in `.env`

Poi inizializza le tabelle:
```bash
python src/models/database.py
```

**Output atteso:**
```
✅ Database tables created successfully!
```

---

### Passo 5: Raccogliere i Dati

Scegli una delle seguenti opzioni:

#### Opzione Quick (30 giorni - Consigliato per iniziare)
```bash
python run_data_collection.py --quick
```
- ⏱️ Tempo: ~5-10 minuti
- 📊 API calls: ~50-80
- ✅ Perfetto per testare il sistema

#### Opzione Standard (6 mesi)
```bash
python run_data_collection.py --months 6
```
- ⏱️ Tempo: ~20-30 minuti
- 📊 API calls: ~150-200
- ⚠️ Potrebbe richiedere 2 giorni con piano free (100 req/giorno)

#### Opzione Completa (12 mesi)
```bash
python run_data_collection.py --months 12
```
- ⏱️ Tempo: ~40-60 minuti
- 📊 API calls: ~300-400
- ⚠️ Richiede 3-4 giorni con piano free

**Durante la raccolta vedrai:**
```
============================================================
🚀 STARTING HISTORICAL DATA COLLECTION
============================================================
Season: 2024
Months back: 1
Include statistics: False
============================================================

🏆 Fetching leagues for season 2024...
   ✅ Added Premier League
   ✅ Added Serie A
   ...

⚽ Fetching teams for Premier League...
   ✅ Added 20 teams

📅 Fetching FT matches for Premier League...
   Found 38 fixtures from API
   ✅ Added 38 new matches
...

============================================================
📊 DATA COLLECTION SUMMARY
============================================================
✅ Leagues added: 5
✅ Teams added: 100
✅ Matches added: 190
❌ Errors: 0
============================================================
```

---

### Passo 6: Verificare i Dati

```bash
python verify_data.py
```

**Output atteso:**
```
============================================================
  📊 DATABASE VERIFICATION
============================================================

✅ Leagues: 5
   - Premier League (England) - Season 2024
   - Serie A (Italy) - Season 2024
   - La Liga (Spain) - Season 2024
   - Bundesliga (Germany) - Season 2024
   - Ligue 1 (France) - Season 2024

✅ Teams: 100
   - Premier League: 20 teams
   - Serie A: 20 teams
   ...

✅ Matches: 190
   - Premier League: 38 total (38 finished, 0 upcoming)
   ...

📅 Recent Matches:
   - Manchester City vs Liverpool: 2-1
     Date: 2024-11-25 15:00 | Status: FT
   ...

============================================================
  ✅ VERIFICATION COMPLETE
============================================================

✨ Database contains 190 matches across 5 leagues!
   Ready for ML model training!
```

---

## 🎯 Avviare l'Applicazione

### Backend API

```bash
cd backend
source venv/bin/activate
python src/api/main.py
```

Apri http://localhost:8000/docs per vedere l'API

### Frontend

In un **nuovo terminale**:

```bash
cd frontend

# Installa dipendenze (solo la prima volta)
npm install

# Avvia il frontend
npm run dev
```

Apri http://localhost:5173 per vedere l'applicazione!

---

## 🐛 Risoluzione Problemi

### "Invalid API Key"
```
❌ Error: 401 Unauthorized
```
**Soluzioni:**
1. Verifica che la chiave in `.env` sia corretta
2. Controlla che non ci siano spazi extra
3. Verifica la sottoscrizione su RapidAPI

### "Rate Limit Exceeded"
```
❌ Error: 429 Too Many Requests
```
**Soluzioni:**
1. Hai esaurito le 100 richieste giornaliere
2. Aspetta 24 ore per il reset
3. Oppure aggiorna al piano Pro su RapidAPI

### "No Data Collected"
```
✅ Matches added: 0
```
**Possibili cause:**
1. Nessuna partita nell'intervallo di date selezionato
2. Prova con `--months 6` invece di `--quick`
3. Controlla che le squadre siano state raccolte

### "Database Connection Error"
```
❌ Error: could not connect to server
```
**Soluzioni:**
1. Avvia PostgreSQL: `docker-compose up -d postgres`
2. Verifica `DATABASE_URL` in `.env`
3. Se usi PostgreSQL locale, verifica che sia in esecuzione

### "Module not found"
```
❌ ModuleNotFoundError: No module named 'fastapi'
```
**Soluzione:**
```bash
# Assicurati di aver attivato il virtual environment
source venv/bin/activate

# Reinstalla le dipendenze
pip install -r requirements.txt
```

---

## 💡 Suggerimenti

### Risparmia API Calls
1. Inizia sempre con `--quick`
2. Non usare `--statistics` inizialmente
3. Espandi gradualmente i dati raccolti

### Monitoraggio API Usage
- Vai su [RapidAPI Dashboard](https://rapidapi.com/developer/apps)
- Controlla il tuo utilizzo giornaliero
- Il limite si resetta ogni 24 ore

### Raccolta Incrementale
```bash
# Giorno 1
python run_data_collection.py --quick

# Giorno 2 (dopo reset quota)
python run_data_collection.py --months 2

# Giorno 3
python run_data_collection.py --months 6
```

### Aggiornamenti Automatici
Una volta raccolti i dati iniziali, avvia lo scheduler:
```bash
python src/data_collection/scheduler.py
```
Questo aggiornerà automaticamente i dati ogni giorno.

---

## ✅ Checklist Completa

Prima di iniziare:
- [ ] Account RapidAPI creato
- [ ] Sottoscrizione API-Football attiva (free tier)
- [ ] API key copiata
- [ ] Virtual environment attivato
- [ ] File `.env` creato e configurato
- [ ] PostgreSQL in esecuzione

Dopo la configurazione:
- [ ] Test API passato (`python src/data_collection/api_client.py`)
- [ ] Database inizializzato (`python src/models/database.py`)
- [ ] Dati raccolti (`python run_data_collection.py --quick`)
- [ ] Verifica completata (`python verify_data.py`)
- [ ] Backend avviato (`python src/api/main.py`)
- [ ] Frontend avviato (`npm run dev`)
- [ ] Applicazione accessibile su http://localhost:5173

---

## 🆘 Hai Ancora Problemi?

1. Controlla i log in `logs/app.log`
2. Rivedi [DATA_COLLECTION.md](DATA_COLLECTION.md)
3. Consulta [SETUP.md](SETUP.md)

---

**🎉 Una volta completati tutti i passaggi, sei pronto per usare il sistema!**
