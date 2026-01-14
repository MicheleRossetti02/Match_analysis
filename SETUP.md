# 🚀 Setup Guide - Football Match Prediction System

Complete guide to get the project up and running.

---

## 📋 Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and npm installed  
- **PostgreSQL** (or use Docker)
- **Redis** (optional, or use Docker)
- **API-Football Key** from [RapidAPI](https://rapidapi.com/api-sports/api/api-football)

---

## ⚡ Quick Start with Docker (Recommended)

### 1. Clone and Setup Environment

```bash
cd Match_analysis

# Create environment file for backend
cp backend/.env.example backend/.env
```

### 2. Configure API Key

Edit `backend/.env` and add your API-Football key:

```env
API_FOOTBALL_KEY=your_actual_api_key_here
```

### 3. Start All Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Backend API (port 8000)
- Frontend app (port 5173)

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

---

## 🔧 Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API_FOOTBALL_KEY

# Initialize database
python src/models/database.py

# Run the server
python src/api/main.py
```

The API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

---

## 📊 Initial Data Collection

### Option 1: Using Python Script

```bash
cd backend
source venv/bin/activate
python src/data_collection/api_client.py
```

This will test the API connection and fetch sample data.

### Option 2: Implement Data Collection Script

Create `backend/src/data_collection/collect_data.py`:

```python
from api_client import APIFootballClient
from src.models.database import SessionLocal, League, Team, Match
import sys
sys.path.append('..')
from config import settings

def collect_initial_data():
    client = APIFootballClient()
    db = SessionLocal()
    
    try:
        # Fetch leagues
        for league_key, league_info in settings.LEAGUES.items():
            print(f"Fetching {league_info['name']}...")
            
            # Fetch and store league data
            leagues_data = client.get_leagues(season=2024)
            
            # Fetch teams
            teams_data = client.get_teams(league_info['id'], season=2024)
            
            # Fetch recent matches
            matches_data = client.get_finished_fixtures(
                league_info['id'], 
                season=2024, 
                last_days=90
            )
            
        print("✅ Data collection completed!")
        
    finally:
        db.close()
        client.close()

if __name__ == "__main__":
    collect_initial_data()
```

---

## 🧪 Testing the Setup

### Test Backend API

```bash
# Health check
curl http://localhost:8000/api/health

# Get leagues  
curl http://localhost:8000/api/leagues

# Check API docs
open http://localhost:8000/docs
```

### Test Frontend

1. Open http://localhost:5173
2. You should see the dashboard
3. Navigate to Statistics page
4. Try selecting a league (once data is loaded)

---

## 🔑 Getting API-Football Key

1. Go to [RapidAPI](https://rapidapi.com/api-sports/api/api-football)
2. Sign up for free account
3. Subscribe to API-Football (free tier: 100 requests/day)
4. Copy your API key
5. Add it to `backend/.env` as `API_FOOTBALL_KEY`

---

## 📦 Project Structure

```
Match_analysis/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/               # API endpoints
│   │   ├── data_collection/   # Data fetching
│   │   ├── ml/                # ML models (coming soon)
│   │   ├── models/            # Database models
│   │   └── utils/             # Utilities
│   ├── requirements.txt
│   └── config.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── data/                       # Data storage
├── models/                     # Trained ML models
└── docker-compose.yml
```

---

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Start PostgreSQL manually
# Or check docker-compose logs
docker-compose logs postgres
```

### API Rate Limit Error

- Free tier limited to 100 requests/day
- Consider upgrading plan or implementing aggressive caching
- Use `min_request_interval` in API client to control rate

### Frontend Not Loading

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### CORS Errors

Check `backend/config.py` CORS_ORIGINS includes your frontend URL.

---

## 📈 Next Steps

After setup:

1. ✅ **Collect Historical Data** - Run data collection script
2. 🤖 **Train ML Models** - Implement and train prediction models
3. 📊 **Generate Predictions** - Create predictions for upcoming matches
4. 🔄 **Setup Automation** - Configure scheduled jobs for data updates
5. 🚀 **Deploy** - Deploy to production environment

---

## 🆘 Need Help?

Check the documentation:
- [Implementation Plan](../implementation_plan.md)
- [FastAPI Docs](http://localhost:8000/docs)
- [API-Football Docs](https://www.api-football.com/documentation-v3)

---

## 📝 Notes

- **Development Mode**: Both frontend and backend run with hot reload
- **Production**: Use `npm run build` for frontend and proper Python server config
- **Database**: PostgreSQL recommended for production, SQLite OK for testing
- **API Limits**: Monitor your API usage to avoid hitting rate limits

**Happy Coding! ⚽🎯**
