"""
Data Collector - Fetch and store football data from API-Football
"""
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api_client import APIFootballClient
from src.models.database import (
    SessionLocal, League, Team, Match, MatchStatistics,
    init_db
)
from config import settings


class DataCollector:
    """Collects and stores football data from API-Football"""
    
    def __init__(self):
        self.client = APIFootballClient()
        self.db = SessionLocal()
        self.stats = {
            'leagues_added': 0,
            'teams_added': 0,
            'matches_added': 0,
            'statistics_added': 0,
            'errors': 0
        }
    
    def close(self):
        """Close database and API client connections"""
        self.db.close()
        self.client.close()
    
    def print_stats(self):
        """Print collection statistics"""
        print("\n" + "="*60)
        print("📊 DATA COLLECTION SUMMARY")
        print("="*60)
        print(f"✅ Leagues added: {self.stats['leagues_added']}")
        print(f"✅ Teams added: {self.stats['teams_added']}")
        print(f"✅ Matches added: {self.stats['matches_added']}")
        print(f"✅ Match Statistics added: {self.stats['statistics_added']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("="*60 + "\n")
    
    def collect_leagues(self, season: int = 2024) -> List[League]:
        """
        Fetch and store league information
        
        Args:
            season: Season year (default: 2024)
            
        Returns:
            List of League objects
        """
        print(f"\n🏆 Fetching leagues for season {season}...")
        leagues = []
        
        for league_key, league_info in settings.LEAGUES.items():
            try:
                # Check if league already exists
                existing = self.db.query(League).filter(
                    League.api_id == league_info["id"],
                    League.season == season
                ).first()
                
                if existing:
                    print(f"   ⏭️  {league_info['name']} already in database")
                    leagues.append(existing)
                    continue
                
                # Fetch from API
                api_leagues = self.client.get_leagues(season=season)
                
                # Find matching league (by code for football-data.org)
                league_data = next(
                    (l for l in api_leagues if l['league']['code'] == league_info['id']),
                    None
                )
                
                if league_data:
                    league = League(
                        api_id=str(league_data['league']['id']),
                        name=league_data['league']['name'],
                        country=league_data['country']['name'],
                        logo=league_data['league'].get('emblem', ''),
                        season=season
                    )
                    
                    self.db.add(league)
                    self.db.commit()
                    self.db.refresh(league)
                    
                    leagues.append(league)
                    self.stats['leagues_added'] += 1
                    print(f"   ✅ Added {league.name}")
                else:
                    print(f"   ⚠️  {league_info['name']} not found in API response")
                    
            except Exception as e:
                print(f"   ❌ Error fetching {league_info['name']}: {e}")
                self.stats['errors'] += 1
        
        return leagues
    
    def collect_teams(self, league: League) -> List[Team]:
        """
        Fetch and store teams for a league
        
        Args:
            league: League object
            
        Returns:
            List of Team objects
        """
        print(f"\n⚽ Fetching teams for {league.name}...")
        teams = []
        
        try:
            # Fetch teams from API (use league code for football-data.org)
            api_teams = self.client.get_teams(league.api_id, season=league.season)
            
            for team_data in api_teams:
                try:
                    team_info = team_data['team']
                    
                    # Check if team already exists
                    existing = self.db.query(Team).filter(
                        Team.api_id == team_info['id']
                    ).first()
                    
                    if existing:
                        # Update league_id if needed
                        if existing.league_id != league.id:
                            existing.league_id = league.id
                            self.db.commit()
                        teams.append(existing)
                        continue
                    
                    # Create new team
                    team = Team(
                        api_id=team_info['id'],
                        name=team_info['name'],
                        code=team_info.get('code'),
                        country=team_info.get('country'),
                        logo=team_info.get('logo'),
                        league_id=league.id
                    )
                    
                    self.db.add(team)
                    self.db.commit()
                    self.db.refresh(team)
                    
                    teams.append(team)
                    self.stats['teams_added'] += 1
                    
                except Exception as e:
                    print(f"   ❌ Error adding team: {e}")
                    self.stats['errors'] += 1
            
            print(f"   ✅ Added {self.stats['teams_added']} teams")
            
        except Exception as e:
            print(f"   ❌ Error fetching teams: {e}")
            self.stats['errors'] += 1
        
        return teams
    
    def collect_matches(
        self, 
        league: League,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        status: str = "FT"
    ) -> List[Match]:
        """
        Fetch and store matches for a league
        
        Args:
            league: League object
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            status: Match status (FT=Finished, NS=Not Started, etc.)
            
        Returns:
            List of Match objects
        """
        print(f"\n📅 Fetching {status} matches for {league.name}...")
        if from_date and to_date:
            print(f"   Date range: {from_date} to {to_date}")
        
        matches = []
        
        try:
            # Fetch fixtures from API (use league code for football-data.org)
            api_fixtures = self.client.get_fixtures(
                league_code=league.api_id,
                season=league.season,
                from_date=from_date,
                to_date=to_date,
                status="FINISHED" if status == "FT" else "SCHEDULED"
            )
            
            print(f"   Found {len(api_fixtures)} fixtures from API")
            
            for fixture_data in api_fixtures:
                try:
                    fixture = fixture_data['fixture']
                    teams = fixture_data['teams']
                    goals = fixture_data['goals']
                    score = fixture_data.get('score', {})
                    
                    # Check if match already exists
                    existing = self.db.query(Match).filter(
                        Match.api_id == fixture['id']
                    ).first()
                    
                    if existing:
                        # Update if status changed
                        if existing.status != fixture['status']['short']:
                            existing.status = fixture['status']['short']
                            existing.home_goals = goals.get('home')
                            existing.away_goals = goals.get('away')
                            existing.updated_at = datetime.utcnow()
                            self.db.commit()
                        continue
                    
                    # Find home and away teams
                    home_team = self.db.query(Team).filter(
                        Team.api_id == teams['home']['id']
                    ).first()
                    
                    away_team = self.db.query(Team).filter(
                        Team.api_id == teams['away']['id']
                    ).first()
                    
                    if not home_team or not away_team:
                        print(f"   ⚠️  Skipping match - teams not found")
                        continue
                    
                    # Create match
                    match = Match(
                        api_id=fixture['id'],
                        league_id=league.id,
                        season=league.season,
                        match_date=datetime.fromisoformat(
                            fixture['date'].replace('Z', '+00:00')
                        ),
                        round=fixture.get('round'),
                        status=fixture['status']['short'],
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        home_goals=goals.get('home'),
                        away_goals=goals.get('away'),
                        home_goals_halftime=score.get('halftime', {}).get('home'),
                        away_goals_halftime=score.get('halftime', {}).get('away')
                    )
                    
                    self.db.add(match)
                    self.db.commit()
                    self.db.refresh(match)
                    
                    matches.append(match)
                    self.stats['matches_added'] += 1
                    
                    # Fetch match statistics if finished
                    if status == "FT" and self.stats['matches_added'] % 10 == 0:
                        # Don't fetch stats for every match to save API calls
                        # Can be done in a separate pass
                        pass
                    
                except Exception as e:
                    print(f"   ❌ Error adding match: {e}")
                    self.stats['errors'] += 1
            
            print(f"   ✅ Added {len(matches)} new matches")
            
        except Exception as e:
            print(f"   ❌ Error fetching matches: {e}")
            self.stats['errors'] += 1
        
        return matches
    
    def collect_match_statistics(self, match: Match) -> Optional[MatchStatistics]:
        """
        Fetch and store detailed statistics for a match
        
        Args:
            match: Match object
            
        Returns:
            MatchStatistics object or None
        """
        try:
            # Check if statistics already exist
            existing = self.db.query(MatchStatistics).filter(
                MatchStatistics.match_id == match.id
            ).first()
            
            if existing:
                return existing
            
            # Fetch from API
            api_stats = self.client.get_fixture_statistics(match.api_id)
            
            if not api_stats or len(api_stats) < 2:
                return None
            
            home_stats = api_stats[0]['statistics']
            away_stats = api_stats[1]['statistics']
            
            def get_stat(stats_list, stat_type):
                """Extract stat value from API response"""
                stat = next((s for s in stats_list if s['type'] == stat_type), None)
                if not stat:
                    return None
                value = stat.get('value')
                if value is None or value == '':
                    return None
                if isinstance(value, str):
                    value = value.replace('%', '')
                try:
                    return float(value) if '.' in str(value) else int(value)
                except:
                    return None
            
            # Create statistics record
            stats = MatchStatistics(
                match_id=match.id,
                home_possession=get_stat(home_stats, 'Ball Possession'),
                home_shots_total=get_stat(home_stats, 'Total Shots'),
                home_shots_on_target=get_stat(home_stats, 'Shots on Goal'),
                home_corners=get_stat(home_stats, 'Corner Kicks'),
                home_fouls=get_stat(home_stats, 'Fouls'),
                home_yellow_cards=get_stat(home_stats, 'Yellow Cards'),
                home_red_cards=get_stat(home_stats, 'Red Cards'),
                home_offsides=get_stat(home_stats, 'Offsides'),
                home_passes_total=get_stat(home_stats, 'Total passes'),
                home_passes_accurate=get_stat(home_stats, 'Passes accurate'),
                away_possession=get_stat(away_stats, 'Ball Possession'),
                away_shots_total=get_stat(away_stats, 'Total Shots'),
                away_shots_on_target=get_stat(away_stats, 'Shots on Goal'),
                away_corners=get_stat(away_stats, 'Corner Kicks'),
                away_fouls=get_stat(away_stats, 'Fouls'),
                away_yellow_cards=get_stat(away_stats, 'Yellow Cards'),
                away_red_cards=get_stat(away_stats, 'Red Cards'),
                away_offsides=get_stat(away_stats, 'Offsides'),
                away_passes_total=get_stat(away_stats, 'Total passes'),
                away_passes_accurate=get_stat(away_stats, 'Passes accurate')
            )
            
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
            
            self.stats['statistics_added'] += 1
            return stats
            
        except Exception as e:
            print(f"   ❌ Error fetching match statistics: {e}")
            self.stats['errors'] += 1
            return None
    
    def collect_historical_data(
        self,
        season: int = 2024,
        months_back: int = 6,
        include_statistics: bool = False
    ):
        """
        Collect historical data for all leagues
        
        Args:
            season: Season year
            months_back: How many months of data to collect
            include_statistics: Whether to fetch detailed match statistics
        """
        print("\n" + "="*60)
        print("🚀 STARTING HISTORICAL DATA COLLECTION")
        print("="*60)
        print(f"Season: {season}")
        print(f"Months back: {months_back}")
        print(f"Include statistics: {include_statistics}")
        print("="*60)
        
        # Initialize database
        init_db()
        
        # Collect leagues
        leagues = self.collect_leagues(season)
        
        if not leagues:
            print("\n❌ No leagues found. Aborting.")
            return
        
        # For each league, collect teams and matches
        for league in leagues:
            print(f"\n{'='*60}")
            print(f"Processing: {league.name}")
            print(f"{'='*60}")
            
            # Collect teams
            teams = self.collect_teams(league)
            
            if not teams:
                print(f"⚠️  No teams found for {league.name}. Skipping matches.")
                continue
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months_back)
            
            # Collect finished matches
            matches = self.collect_matches(
                league=league,
                from_date=start_date.strftime("%Y-%m-%d"),
                to_date=end_date.strftime("%Y-%m-%d"),
                status="FT"
            )
            
            # Collect upcoming matches
            future_date = end_date + timedelta(days=14)
            upcoming = self.collect_matches(
                league=league,
                from_date=end_date.strftime("%Y-%m-%d"),
                to_date=future_date.strftime("%Y-%m-%d"),
                status="NS"
            )
            
            # Optionally collect statistics
            if include_statistics and matches:
                print(f"\n📊 Collecting statistics for finished matches...")
                # Only collect for a sample to save API calls
                sample_size = min(20, len(matches))
                print(f"   Collecting stats for {sample_size} matches (sample)")
                
                for match in matches[:sample_size]:
                    self.collect_match_statistics(match)
                    time.sleep(1)  # Respect rate limits
        
        # Print final statistics
        self.print_stats()


def main():
    """Main function to run data collection"""
    collector = DataCollector()
    
    try:
        # Collect last 6 months of data
        # Set include_statistics=True if you want detailed stats (uses more API calls)
        collector.collect_historical_data(
            season=2024,
            months_back=6,
            include_statistics=False  # Set to True if you have enough API quota
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()
        print("\n✅ Data collection completed!\n")


if __name__ == "__main__":
    main()
