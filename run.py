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

def run_extract_club_process():
    """Run the extract club script to process club data"""
    print("\n" + "="*60)
    print("Running extract_club.py ...")
    print("="*60 + "\n")
    
    result = subprocess.run([
        'python', 'data_preparation/extract_clubs.py'
    ])
    
    return result.returncode == 0

def run_create_sequence_process():
    """Run the script to create players transfer sequence"""
    print("\n" + "="*60)
    print("Running create_sequence.py ...")
    print("="*60 + "\n")
    
    result = subprocess.run([
        'python', 'data_preparation/create_sequence.py'
    ])
    
    return result.returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py [players|transfers|all|extract_club|create_sequence]")
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
    
    elif command == 'extract_club':
        success = run_extract_club_process()
        if success:
            print("\n✓ Extracting club data successful!")
        else:
            print("\n✗ Club extraction failed!")
            sys.exit(1)
    
    elif command == 'create_sequence':
        success = run_create_sequence_process()
        if success:
            print("\n✓ Players transfer sequence created successfuly!")
        else:
            print("\n✗ Transfer sequence creation failed!")
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