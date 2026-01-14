# 📊 Data Collection Guide

Complete guide for collecting football match data from API-Football.

---

## 🎯 Overview

The data collection system fetches and stores:
- ⚽ **5 European Leagues** (Premier League, Serie A, La Liga, Bundesliga, Ligue 1)
- 🏟️ **Teams** with logos and metadata
- 📅 **Matches** with results and schedules
- 📊 **Statistics** (possession, shots, cards, etc.)

---

## 🔑 Step 1: Get API Key

1. Go to [RapidAPI - API-Football](https://rapidapi.com/api-sports/api/api-football)
2. Sign up for a free account
3. Subscribe to **API-Football** (free tier: 100 requests/day)
4. Copy your **X-RapidAPI-Key**

---

## ⚙️ Step 2: Configure Environment

```bash
cd backend

# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use any text editor
```

Add your key to `.env`:

```env
API_FOOTBALL_KEY=your_actual_api_key_here
```

---

## 🚀 Step 3: Run Data Collection

### Option A: Quick Start (Recommended for Testing)

Collects last 30 days only:

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Quick collection
python run_data_collection.py --quick
```

### Option B: Full Historical Data

Collects last 6 months (may take 2-3 days with free API tier):

```bash
python run_data_collection.py --months 6
```

### Option C: With Detailed Statistics

⚠️ **Warning**: Uses significantly more API calls

```bash
python run_data_collection.py --statistics
```

### Custom Options

```bash
# Custom season and time range
python run_data_collection.py --season 2024 --months 12

# Different season
python run_data_collection.py --season 2023 --months 6
```

---

## 📊 Step 4: Verify Data

Check what data was collected:

```bash
python verify_data.py
```

This will show:
- Number of leagues, teams, and matches
- Recent and upcoming matches
- Sample statistics

---

## 🔄 Step 5: Automated Updates (Optional)

For continuous data updates:

```bash
python src/data_collection/scheduler.py
```

This runs:
- **Daily at 3:00 AM**: Update matches
- **Weekly on Sunday at 2:00 AM**: Collect statistics

Press `Ctrl+C` to stop.

---

## 📈 Expected Results

After successful collection, you should see:

```
📊 DATA COLLECTION SUMMARY
============================================================
✅ Leagues added: 5
✅ Teams added: ~100
✅ Matches added: 150-300 (depending on time range)
✅ Match Statistics added: 0-50 (if --statistics used)
❌ Errors: 0
============================================================
```

---

## 🔍 Verify via API

Start the backend:

```bash
python src/api/main.py
```

Check the API:
- **Leagues**: http://localhost:8000/api/leagues
- **Teams**: http://localhost:8000/api/leagues/1/teams
- **Matches**: http://localhost:8000/api/leagues/1/matches
- **API Docs**: http://localhost:8000/docs

---

## 💡 Pro Tips

### 1. Start Small
- Use `--quick` for initial testing
- Verify everything works before collecting more data

### 2. Monitor API Usage
- Free tier: 100 requests/day
- Each league needs ~20-40 requests for initial setup
- Track your usage on RapidAPI dashboard

### 3. Incremental Collection
```bash
# Day 1: Quick test
python run_data_collection.py --quick

# Day 2: Last 2 months
python run_data_collection.py --months 2

# Day 3: Last 6 months
python run_data_collection.py --months 6
```

### 4. Skip Statistics Initially
- Statistics use many API calls
- Start without `--statistics`
- Add later when you have upgraded API plan

---

## 🐛 Troubleshooting

### "Invalid API Key"
- Check your API key in `.env`
- Ensure no extra spaces
- Verify subscription is active on RapidAPI

### "Rate Limit Exceeded"
```
❌ Error: 429 Too Many Requests
```
- You've hit daily quota (100 requests)
- Wait 24 hours or upgrade plan
- Use `--quick` to reduce API calls

### "No Data Collected"
- Check internet connection
- Verify API key is correct
- Try running `python src/data_collection/api_client.py` to test connection

### Database Connection Error
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Try: `docker-compose up -d postgres`

---

## 📊 Data Collection Progress

The collector shows real-time progress:

```
🏆 Fetching leagues for season 2024...
   ✅ Added Premier League
   ✅ Added Serie A
   ✅ Added La Liga
   ✅ Added Bundesliga
   ✅ Added Ligue 1

⚽ Fetching teams for Premier League...
   ✅ Added 20 teams

📅 Fetching FT matches for Premier League...
   Found 150 fixtures from API
   ✅ Added 150 new matches
```

---

## 🎯 Next Steps

After data collection:

1. ✅ **Verify data** - Run `python verify_data.py`
2. 🤖 **Implement ML models** - Create prediction algorithms
3. 📊 **Train models** - Use historical data for training
4. 🔮 **Generate predictions** - Predict upcoming matches
5. 🌐 **View in frontend** - See data at http://localhost:5173

---

## 📝 Collection Strategies

### Strategy 1: Conservative (Free Tier)

```bash
# Week 1: Setup and test
python run_data_collection.py --quick

# Week 2: Gradual expansion
python run_data_collection.py --months 2

# Week 3 onwards: Automated updates
python src/data_collection/scheduler.py
```

### Strategy 2: Aggressive (Paid Tier)

```bash
# Collect everything at once
python run_data_collection.py --months 12 --statistics

# Start scheduler
python src/data_collection/scheduler.py
```

---

## ✅ Checklist

Before running collection:
- [ ] API key obtained from RapidAPI
- [ ] `.env` file configured with API key
- [ ] Virtual environment activated
- [ ] PostgreSQL running

After collection:
- [ ] Run `verify_data.py` to check results
- [ ] Check API for data via `/docs`
- [ ] View leagues and matches in frontend
- [ ] Optionally start scheduler for updates

---

## 📞 Support

**Issues?**
- Check [backend/src/data_collection/README.md](backend/src/data_collection/README.md)
- Review API logs in `logs/app.log`
- Test API connection: `python src/data_collection/api_client.py`

**API-Football Documentation:**
- https://www.api-football.com/documentation-v3

---

**🎉 Happy Data Collecting!**
