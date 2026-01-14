# Football Match Prediction System ⚽

Sistema di Machine Learning per la predizione dei risultati delle partite dei **Top 5 campionati europei**.

## 🎯 Campionati Supportati

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League** (Inghilterra)
- 🇮🇹 **Serie A** (Italia)
- 🇪🇸 **La Liga** (Spagna)
- 🇩🇪 **Bundesliga** (Germania)
- 🇫🇷 **Ligue 1** (Francia)

## 🏗️ Architettura

- **Backend**: FastAPI + Python 3.10+
- **Database**: PostgreSQL
- **Cache**: Redis
- **ML**: Scikit-learn, XGBoost, TensorFlow
- **Frontend**: React + Vite + TailwindCSS

## 📦 Struttura Progetto

```
Match_analysis/
├── backend/          # API e ML pipeline
├── frontend/         # Dashboard React
├── data/            # Dati locali e cache
├── models/          # Modelli ML salvati
└── docker-compose.yml
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your API_FOOTBALL_KEY

# Frontend setup
cd ../frontend
npm install
```

### 2. Collect Data

Get your API key from [RapidAPI](https://rapidapi.com/api-sports/api/api-football), then:

```bash
cd backend
source venv/bin/activate

# Quick test (last 30 days)
python run_data_collection.py --quick

# Or full historical data
python run_data_collection.py --months 6
```

See [DATA_COLLECTION.md](DATA_COLLECTION.md) for detailed instructions.

### 3. Start Application

**Option A: Docker (Recommended)**
```bash
docker-compose up -d
```

**Option B: Manual**
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python src/api/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## 📖 Documentazione

- [Piano di Implementazione](docs/implementation_plan.md)
- [API Documentation](http://localhost:8000/docs) (quando il server è attivo)

## 🎯 Features

- ✅ Predizioni per partite imminenti
- ✅ Analisi statistiche dettagliate
- ✅ Storico performance modelli
- ✅ Aggiornamento automatico dati
- ✅ Dashboard interattiva

## 📊 Performance Modelli

Target: **Accuracy > 55%** (baseline bookmaker ~52%)

## 🔄 Aggiornamenti

I dati vengono aggiornati automaticamente:
- **Giornaliero** (3:00 AM): Risultati e statistiche
- **Bi-settimanale**: Retraining modelli ML
- **Pre-match** (2h prima): Generazione predizioni

## 📝 License

MIT License
