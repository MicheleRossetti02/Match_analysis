#!/usr/bin/env python3
"""
Quick script to run data collection
Usage: python run_data_collection.py [options]
"""
import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.data_collector import DataCollector


def main():
    parser = argparse.ArgumentParser(description='Collect football match data')
    parser.add_argument(
        '--season',
        type=int,
        default=2024,
        help='Season year (default: 2024)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='Number of months of historical data to collect (default: 6)'
    )
    parser.add_argument(
        '--statistics',
        action='store_true',
        help='Collect detailed match statistics (uses more API calls)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: only collect last 30 days'
    )
    
    args = parser.parse_args()
    
    # Adjust for quick mode
    if args.quick:
        args.months = 1
        print("🚀 Quick mode: collecting last 30 days only\n")
    
    # Run collection
    collector = DataCollector()
    
    try:
        collector.collect_historical_data(
            season=args.season,
            months_back=args.months,
            include_statistics=args.statistics
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        collector.close()
    
    print("\n✅ Data collection completed successfully!\n")


if __name__ == "__main__":
    main()
