# Data Collection Module 📊

This module handles fetching football data from API-Football and storing it in the database.

## 🎯 Features

- Fetch leagues, teams, matches, and statistics
- Automatic rate limiting to respect API quotas
- Error handling and retry logic
- Progress tracking and statistics
- Scheduled automatic updates

## 📋 Files

- **`api_client.py`** - API-Football client wrapper
- **`data_collector.py`** - Main data collection logic
- **`scheduler.py`** - Automated scheduling for updates

## 🚀 Quick Start

### One-Time Historical Collection

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run collection (last 6 months)
python run_data_collection.py

# Quick mode (last 30 days only)
python run_data_collection.py --quick

# With detailed statistics
python run_data_collection.py --statistics

# Custom time range
python run_data_collection.py --season 2024 --months 12
```

### Testing API Connection

```bash
python src/data_collection/api_client.py
```

This will test your API key and fetch sample data.

## 📅 Automated Scheduling

To run automatic daily updates:

```bash
python src/data_collection/scheduler.py
```

This will schedule:
- **Daily at 3:00 AM**: Update recent matches and upcoming fixtures
- **Weekly on Sunday at 2:00 AM**: Collect detailed match statistics

Press `Ctrl+C` to stop the scheduler.

## 🔧 Configuration

### API Key Setup

1. Get your API key from [RapidAPI](https://rapidapi.com/api-sports/api/api-football)
2. Add to `backend/.env`:

```env
API_FOOTBALL_KEY=your_key_here
```

### Rate Limits

- **Free Tier**: 100 requests/day
- **Pro Tier**: 3000+ requests/day

The client automatically enforces a 1-second delay between requests.

## 📊 What Data is Collected

### Leagues
- Name, country, logo
- Season information

### Teams
- Name, code, country
- Team logo
- League association

### Matches
- Date and time
- Home and away teams
- Final score
- Halftime score
- Match status (FT, NS, LIVE, etc.)
- Round information

### Match Statistics (Optional)
- Possession %
- Shots (total and on target)
- Corners
- Fouls
- Cards (yellow/red)
- Offsides
- Passes (total and accurate)

## 💡 Tips

### Optimize API Usage

1. **Quick Mode**: For testing, use `--quick` to only fetch last 30 days
2. **Skip Statistics**: Don't use `--statistics` unless you have a paid plan
3. **Scheduled Updates**: Use the scheduler instead of manual runs

### Monitor Progress

The collector prints detailed progress:
- ✅ Successfully added items
- ⏭️ Already existing items (skipped)
- ❌ Errors encountered

### Check Database

After collection, verify data in database:

```python
from src.models.database import SessionLocal, League, Team, Match

db = SessionLocal()

# Count leagues
print(f"Leagues: {db.query(League).count()}")

# Count teams  
print(f"Teams: {db.query(Team).count()}")

# Count matches
print(f"Matches: {db.query(Match).count()}")
```

Or use the API:
- http://localhost:8000/api/leagues
- http://localhost:8000/api/leagues/1/teams
- http://localhost:8000/api/leagues/1/matches

## 🐛 Troubleshooting

### "Invalid API Key" Error

Check your `.env` file has the correct `API_FOOTBALL_KEY`.

### "Rate Limit Exceeded"

You've hit your daily quota. Wait 24 hours or upgrade your plan.

### "No Teams Found"

Make sure to collect leagues first before collecting teams/matches.

### Database Connection Error

Ensure PostgreSQL is running:

```bash
# Using Docker
docker-compose up -d postgres

# Or start manually
pg_ctl start
```

## 📈 Expected API Call Usage

For initial collection (6 months, 5 leagues):

- Leagues: ~5 calls
- Teams: ~100 calls (20 per league)
- Matches: Variable, depends on fixtures in time range

**Estimate**: ~150-200 API calls for initial setup

With free tier (100/day), you may need 2-3 days for complete initial collection.

## 🔄 Update Strategy

**Recommended approach:**

1. **Initial Setup**: Run `--quick` to get last 30 days
2. **Daily**: Let scheduler run automatic updates
3. **Gradual**: Manually run for older months as API quota allows

## 📝 Example Workflow

```bash
# Day 1: Quick setup
python run_data_collection.py --quick

# Start backend to test
python src/api/main.py

# Check data at http://localhost:8000/docs

# Day 2-N: Collect more historical data
python run_data_collection.py --months 2

# Once satisfied: Start scheduler
python src/data_collection/scheduler.py
```

## ✅ Next Steps

After data collection:

1. ✅ Verify data in database
2. 🤖 Implement ML models for predictions
3. 📊 Train models on historical data
4. 🔮 Generate predictions for upcoming matches
