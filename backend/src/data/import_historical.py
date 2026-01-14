"""
Import Historical Football Data from football-data.co.uk
This provides free historical data for European leagues
"""
import os
import sys
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Team, League
from config import settings


# football-data.co.uk URLs for major leagues
# Extended to include 8 seasons (2016-2024) for better training
DATA_URLS = {
    # Premier League
    'england': {
        'league_name': 'Premier League',
        'country': 'England',
        'api_id': 39,
        'urls': [
            'https://www.football-data.co.uk/mmz4281/2324/E0.csv',  # 2023-24
            'https://www.football-data.co.uk/mmz4281/2223/E0.csv',  # 2022-23
            'https://www.football-data.co.uk/mmz4281/2122/E0.csv',  # 2021-22
            'https://www.football-data.co.uk/mmz4281/2021/E0.csv',  # 2020-21
            'https://www.football-data.co.uk/mmz4281/1920/E0.csv',  # 2019-20
            'https://www.football-data.co.uk/mmz4281/1819/E0.csv',  # 2018-19
            'https://www.football-data.co.uk/mmz4281/1718/E0.csv',  # 2017-18
            'https://www.football-data.co.uk/mmz4281/1617/E0.csv',  # 2016-17
        ]
    },
    # Serie A
    'italy': {
        'league_name': 'Serie A',
        'country': 'Italy',
        'api_id': 135,
        'urls': [
            'https://www.football-data.co.uk/mmz4281/2324/I1.csv',
            'https://www.football-data.co.uk/mmz4281/2223/I1.csv',
            'https://www.football-data.co.uk/mmz4281/2122/I1.csv',
            'https://www.football-data.co.uk/mmz4281/2021/I1.csv',
            'https://www.football-data.co.uk/mmz4281/1920/I1.csv',
            'https://www.football-data.co.uk/mmz4281/1819/I1.csv',
            'https://www.football-data.co.uk/mmz4281/1718/I1.csv',
            'https://www.football-data.co.uk/mmz4281/1617/I1.csv',
        ]
    },
    # La Liga
    'spain': {
        'league_name': 'Primera Division',
        'country': 'Spain',
        'api_id': 140,
        'urls': [
            'https://www.football-data.co.uk/mmz4281/2324/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/2223/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/2122/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/2021/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/1920/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/1819/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/1718/SP1.csv',
            'https://www.football-data.co.uk/mmz4281/1617/SP1.csv',
        ]
    },
    # Bundesliga
    'germany': {
        'league_name': 'Bundesliga',
        'country': 'Germany',
        'api_id': 78,
        'urls': [
            'https://www.football-data.co.uk/mmz4281/2324/D1.csv',
            'https://www.football-data.co.uk/mmz4281/2223/D1.csv',
            'https://www.football-data.co.uk/mmz4281/2122/D1.csv',
            'https://www.football-data.co.uk/mmz4281/2021/D1.csv',
            'https://www.football-data.co.uk/mmz4281/1920/D1.csv',
            'https://www.football-data.co.uk/mmz4281/1819/D1.csv',
            'https://www.football-data.co.uk/mmz4281/1718/D1.csv',
            'https://www.football-data.co.uk/mmz4281/1617/D1.csv',
        ]
    },
    # Ligue 1
    'france': {
        'league_name': 'Ligue 1',
        'country': 'France',
        'api_id': 61,
        'urls': [
            'https://www.football-data.co.uk/mmz4281/2324/F1.csv',
            'https://www.football-data.co.uk/mmz4281/2223/F1.csv',
            'https://www.football-data.co.uk/mmz4281/2122/F1.csv',
            'https://www.football-data.co.uk/mmz4281/2021/F1.csv',
            'https://www.football-data.co.uk/mmz4281/1920/F1.csv',
            'https://www.football-data.co.uk/mmz4281/1819/F1.csv',
            'https://www.football-data.co.uk/mmz4281/1718/F1.csv',
            'https://www.football-data.co.uk/mmz4281/1617/F1.csv',
        ]
    }
}


def download_csv(url):
    """Download CSV data from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text), encoding='utf-8', on_bad_lines='skip')
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return None


def get_or_create_team(db, team_name, league_id, country):
    """Get existing team or create new one"""
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        # Create new team with generated API ID
        max_id = db.query(Team).order_by(Team.api_id.desc()).first()
        new_api_id = (max_id.api_id if max_id else 10000) + 1
        
        team = Team(
            api_id=new_api_id,
            name=team_name,
            country=country,
            league_id=league_id
        )
        db.add(team)
        db.flush()
    return team


def import_data_for_league(db, league_config, country_key):
    """Import data for a single league"""
    print(f"\n📊 Importing {league_config['league_name']}...")
    
    # Find or create league
    league = db.query(League).filter(League.api_id == league_config['api_id']).first()
    if not league:
        league = League(
            api_id=league_config['api_id'],
            name=league_config['league_name'],
            country=league_config['country'],
            season=2024
        )
        db.add(league)
        db.flush()
    
    total_imported = 0
    
    for url in league_config['urls']:
        df = download_csv(url)
        if df is None:
            continue
        
        # Determine season from URL
        season_code = url.split('/')[-2]  # e.g., "2324"
        season = 2000 + int(season_code[:2])
        
        print(f"  Processing season {season}/{season+1} ({len(df)} matches)...")
        
        imported = 0
        for _, row in df.iterrows():
            try:
                # Parse date
                date_str = row.get('Date')
                if pd.isna(date_str):
                    continue
                
                # Try different date formats  
                for fmt in ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']:
                    try:
                        match_date = datetime.strptime(str(date_str), fmt)
                        break
                    except:
                        continue
                else:
                    continue
                
                home_team_name = row.get('HomeTeam') or row.get('Home')
                away_team_name = row.get('AwayTeam') or row.get('Away')
                
                if pd.isna(home_team_name) or pd.isna(away_team_name):
                    continue
                
                # Get or create teams
                home_team = get_or_create_team(db, home_team_name, league.id, league_config['country'])
                away_team = get_or_create_team(db, away_team_name, league.id, league_config['country'])
                
                # Check if match already exists
                existing = db.query(Match).filter(
                    Match.home_team_id == home_team.id,
                    Match.away_team_id == away_team.id,
                    Match.match_date == match_date
                ).first()
                
                if existing:
                    continue
                
                # Get goals
                home_goals = row.get('FTHG') if pd.notna(row.get('FTHG')) else row.get('HG')
                away_goals = row.get('FTAG') if pd.notna(row.get('FTAG')) else row.get('AG')
                
                if pd.isna(home_goals) or pd.isna(away_goals):
                    continue
                
                # Create match with unique API ID using UUID
                import uuid
                new_api_id = abs(hash(str(uuid.uuid4()))) % (10**10)  # 10-digit unique int
                
                match = Match(
                    api_id=new_api_id,
                    league_id=league.id,
                    season=season,
                    match_date=match_date,
                    status='FT',
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_goals=int(home_goals),
                    away_goals=int(away_goals)
                )
                db.add(match)
                imported += 1
                
            except Exception as e:
                continue
        
        db.commit()
        total_imported += imported
        print(f"    ✓ Imported {imported} new matches")
    
    return total_imported


def import_all_historical_data():
    """Import historical data for all leagues"""
    print("\n🔄 Importing Historical Football Data...")
    print("=" * 60)
    
    db = SessionLocal()
    
    # Get initial count
    initial_count = db.query(Match).count()
    print(f"Current matches in database: {initial_count}")
    
    total_imported = 0
    
    for country_key, config in DATA_URLS.items():
        imported = import_data_for_league(db, config, country_key)
        total_imported += imported
    
    db.close()
    
    # Final count
    db = SessionLocal()
    final_count = db.query(Match).count()
    finished_count = db.query(Match).filter(Match.status == 'FT').count()
    db.close()
    
    print("\n" + "=" * 60)
    print("📊 IMPORT SUMMARY")
    print("=" * 60)
    print(f"Matches before import: {initial_count}")
    print(f"Matches after import:  {final_count}")
    print(f"New matches added:     {total_imported}")
    print(f"Total finished matches (for training): {finished_count}")
    print("=" * 60)
    
    return total_imported


if __name__ == "__main__":
    import_all_historical_data()
