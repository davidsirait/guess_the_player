#!/usr/bin/env python3
"""
Runner script for Transfermarkt scraper
Usage:
    python run.py players      # Run player spider only
    python run.py transfers    # Run transfer spider only
    python run.py all          # Run both spiders sequentially
"""

import sys
import subprocess


def run_player_spider():
    """Run the player spider to collect player IDs"""
    print("\n" + "="*60)
    print("Running Player Spider...")
    print("="*60 + "\n")
    
    result = subprocess.run([
        'scrapy', 'crawl', 'player_spider'
    ])
    
    return result.returncode == 0


def run_transfer_spider():
    """Run the transfer spider to collect transfer histories"""
    print("\n" + "="*60)
    print("Running Transfer Spider...")
    print("="*60 + "\n")
    
    result = subprocess.run([
        'scrapy', 'crawl', 'transfer_spider',
        '-a', 'player_file=output/players.json'
    ])
    
    return result.returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py [players|transfers|all]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'players':
        success = run_player_spider()
        if success:
            print("\n✓ Player spider completed successfully!")
            print("Output saved to: output/players.json")
        else:
            print("\n✗ Player spider failed!")
            sys.exit(1)
    
    elif command == 'transfers':
        success = run_transfer_spider()
        if success:
            print("\n✓ Transfer spider completed successfully!")
            print("Output saved to: output/transfers.json")
        else:
            print("\n✗ Transfer spider failed!")
            sys.exit(1)
    
    elif command == 'all':
        # Run player spider first
        player_success = run_player_spider()
        
        if not player_success:
            print("\n✗ Player spider failed! Aborting transfer spider.")
            sys.exit(1)
        
        print("\n✓ Player spider completed successfully!")
        print("Output saved to: output/players.json")
        
        # Then run transfer spider
        transfer_success = run_transfer_spider()
        
        if transfer_success:
            print("\n✓ Transfer spider completed successfully!")
            print("Output saved to: output/transfers.json")
            print("\n" + "="*60)
            print("All spiders completed successfully!")
            print("="*60)
        else:
            print("\n✗ Transfer spider failed!")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: python run.py [players|transfers|all]")
        sys.exit(1)


if __name__ == '__main__':
    main()