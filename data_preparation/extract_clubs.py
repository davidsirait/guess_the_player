#!/usr/bin/env python3
"""
Step 1: Extract unique clubs and their logos from transfer_details
Then populate the clubs table
"""

import duckdb
import re
from pathlib import Path


def slugify(text):
    """Convert club name to slug (URL-safe identifier)"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def get_club_id(url):
    """Extract club ID from club URL"""
    try:
        parts = url.split('/')
        # find the last part
        id_part = parts[-1]
        # check if it contains underscore
        if "_" in id_part:
            club_id = id_part.split('_')[0]
            return club_id
        elif "default" in id_part:
            return 0
        elif "." in id_part:
            club_id = id_part.split('.')[0]   
            return club_id 
        return None
    except:
        return None

def create_clubs_table(conn):
    """Create clubs table if it doesn't exist"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            club_id INTEGER PRIMARY KEY,
            club_name VARCHAR,
            logo_url VARCHAR,
            country VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created clubs table")


def extract_clubs_from_transfers(conn):
    """Extract all unique clubs with their logo URLs from transfer_details"""
    
    print("\nExtracting clubs from transfer_details...")
    
    # Get clubs from 'from_club' column
    from_clubs = conn.execute("""
        SELECT DISTINCT 
            from_club as club_name,
            from_club_image_url as logo_url
        FROM transfer_details
        WHERE from_club IS NOT NULL 
          AND from_club_image_url IS NOT NULL
    """).fetchdf()
    
    print(f"  Found {len(from_clubs)} clubs in 'from_club' column")
    
    # Get clubs from 'to_club' column
    to_clubs = conn.execute("""
        SELECT DISTINCT 
            to_club as club_name,
            to_club_image_url as logo_url
        FROM transfer_details
        WHERE to_club IS NOT NULL 
          AND to_club_image_url IS NOT NULL
    """).fetchdf()
    
    print(f"  Found {len(to_clubs)} clubs in 'to_club' column")
    
    # Combine and deduplicate
    import pandas as pd
    all_clubs = pd.concat([from_clubs, to_clubs]).drop_duplicates(subset=['club_name'])
    
    print(f"  Total unique clubs: {len(all_clubs)}")
    
    return all_clubs


def populate_clubs_table(conn, clubs_df):
    """Insert clubs into the clubs table"""
    
    print("\nPopulating clubs table...")
    inserted_count = 0
    skipped_count = 0
    
    for _, row in clubs_df.iterrows():
        club_name = row['club_name']
        logo_url = row['logo_url']
        club_id = get_club_id(row['logo_url'])
        
        try:
            # Check if club already exists
            existing = conn.execute("""
                SELECT club_id FROM clubs WHERE club_id = ?
            """, [club_id]).fetchone()
            
            if existing:
                skipped_count += 1
                continue
            
            # Insert new club
            conn.execute("""
                INSERT INTO clubs (club_id, club_name, logo_url)
                VALUES (?, ?, ?)
            """, [club_id, club_name, logo_url])
            
            inserted_count += 1
            
        except Exception as e:
            print(f"  Error inserting {club_name} with logo_url {logo_url}: {e}")
    
    print(f"  Inserted {inserted_count} clubs")
    print(f"  Skipped {skipped_count} existing clubs")


def show_sample_clubs(conn):
    """Show sample clubs from the table"""
    
    print("\nSample clubs:")
    print("-" * 80)
    
    sample = conn.execute("""
        SELECT club_id, club_name, logo_url
        FROM clubs
        ORDER BY club_name
        LIMIT 10
    """).fetchdf()
    
    for _, row in sample.iterrows():
        print(f"  {row['club_id']:<30} {row['club_name']:<40}")
    
    print("-" * 80)


def show_statistics(conn):
    """Show statistics about clubs"""
    
    print("\nClubs Statistics:")
    print("-" * 80)
    
    total = conn.execute("SELECT COUNT(*) FROM clubs").fetchone()[0]
    print(f"  Total clubs: {total}")
    
    with_logos = conn.execute("""
        SELECT COUNT(*) FROM clubs WHERE logo_url IS NOT NULL
    """).fetchone()[0]
    print(f"  Clubs with logos: {with_logos}")
    
    print("-" * 80)


def main():
    """Main execution"""
    print("="*80)
    print("STEP 1: EXTRACT AND POPULATE CLUBS TABLE")
    print("="*80)
    
    # Connect to database
    db_path = 'transfermarkt.db'
    conn = duckdb.connect(db_path)
    print(f"\n Connected to {db_path}")
    
    # Check if transfer_details table exists
    tables = conn.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'transfer_details'
    """).fetchall()
    
    if not tables:
        print("\n Error: transfer_details table not found!")
        print("   Please run the transfer spider first.")
        return
    
    # Create clubs table
    create_clubs_table(conn)
    
    # Extract clubs from transfer_details
    clubs_df = extract_clubs_from_transfers(conn)
    
    if len(clubs_df) == 0:
        print("\n No clubs found in transfer_details!")
        print("   Make sure you have transfer data with club logo URLs.")
        return
    
    # Populate clubs table
    populate_clubs_table(conn, clubs_df)
    
    # Show results
    show_sample_clubs(conn)
    show_statistics(conn)
    
    conn.close()
    
    print("\n" + "="*80)
    print("STEP 1 COMPLETED!")
    print("="*80)


if __name__ == '__main__':
    main()