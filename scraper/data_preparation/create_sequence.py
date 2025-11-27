#!/usr/bin/env python3
"""
Analyze career sequences for game design (Using transfer_details directly)
Keeps ALL transfers but:
1. Merges loan + permanent to same club
2. Excludes youth/reserve teams
"""

import duckdb
import json
import re


def is_youth_or_reserve_club(club_name):
    """Check if club is a youth/reserve team"""
    if not club_name:
        return False
    
    club_clean = club_name.lower().strip()
    
    youth_keywords = [
        'u16', 'u17', 'u18', 'u19', 'u20', 'u21', 'u22', 'u23',
        'u15', 'sub-15', 'sub-17', 'sub-19', 'sub-20', 'sub-21',
        'youth', 'reserve', 'reserves', 'yth.', 'yth', 'you.', 
        'b team', 'b-team', 'acad.', 'academy', 'ii',
        'ii team', 'ii-team', 'jgd.', 'jong', 'jrs.',
        'under 18', 'under 19', 'under 21', 'under 23',
        'u-18', 'u-19', 'u-21', 'u-23',
        'juvenil', 'juvenile', 'without club'
    ]
    
    if any(keyword in club_clean for keyword in youth_keywords):
        return True
    
    if club_name.endswith(' B') or club_name.endswith(' C') or club_name.endswith(' D'):
        return True


def build_cleaned_sequence(transfers_list):
    """Build sequence with cleaning rules applied"""
    cleaned = []
    i = 0

    while i < len(transfers_list):
        t = transfers_list[i]
        club = t['to_club']
        fee = (t.get('fee') or '').lower()

        if is_youth_or_reserve_club(club):
            i += 1
            continue

        is_loan = 'loan transfer' in fee or (fee and 'loan' in fee and 'end of' not in fee)
        is_end_of_loan = 'end of loan' in fee

        if is_end_of_loan:
            if i + 1 < len(transfers_list):
                next_fee = (transfers_list[i + 1].get('fee') or '').lower()
                if 'loan' in next_fee and 'end of' not in next_fee:
                    i += 1
                    continue
            i += 1
            cleaned.append({
                'club': club,
                'logo': t.get('to_club_image_url'),
                'season': t['season'],
                'fee': t.get('fee', ''),
                'is_loan': False
            })
            continue

        if is_loan:
            j = i + 1
            while j < len(transfers_list):
                next_fee = (transfers_list[j].get('fee') or '').lower()
                next_to = transfers_list[j]['to_club']
                if 'end of loan' in next_fee:
                    j += 1
                    continue
                if next_to == club and 'loan' not in next_fee:
                    cleaned.append({
                        'club': club,
                        'logo': t.get('to_club_image_url'),
                        'season': transfers_list[j]['season'],
                        'fee': transfers_list[j].get('fee', ''),
                        'is_loan': False
                    })
                    i = j + 1
                    break
                else:
                    cleaned.append({
                        'club': club,
                        'logo': t.get('to_club_image_url'),
                        'season': t['season'],
                        'fee': t.get('fee', ''),
                        'is_loan': True
                    })
                    i += 1
                    break
            else:
                cleaned.append({
                    'club': club,
                    'logo': t.get('to_club_image_url'),
                    'season': t['season'],
                    'fee': t.get('fee', ''),
                    'is_loan': True
                })
                i += 1
            continue

        cleaned.append({
            'club': club,
            'logo': t.get('to_club_image_url'),
            'season': t['season'],
            'fee': t.get('fee', ''),
            'is_loan': False
        })
        i += 1

    final_cleaned = []
    for idx, c in enumerate(cleaned):
        if idx == 0 or c['club'] != cleaned[idx - 1]['club']:
            final_cleaned.append(c)

    return final_cleaned


def get_all_sequences(conn):
    """Get all player sequences with cleaning applied"""
    
    print("\nBuilding cleaned sequences from transfer_details...")
    
    players = conn.execute("""
        SELECT 
            DISTINCT player_id, 
            player_name, 
            market_value_numeric
        FROM players
        ORDER BY player_name
    """).fetchdf()
    
    sequences = []
    skipped = 0
    
    for _, player in players.iterrows():
        transfers = conn.execute("""
            SELECT 
                to_club,
                to_club_image_url,
                season,
                transfer_date,
                fee
            FROM transfer_details
            WHERE player_id = ?
              AND to_club IS NOT NULL
            ORDER BY id DESC
        """, [player['player_id']]).fetchdf()
        
        if len(transfers) == 0:
            continue

        transfers_list = transfers.to_dict('records')
        cleaned = build_cleaned_sequence(transfers_list)
        
        if len(cleaned) == 0:
            skipped += 1
            continue
        
        club_names = [t['club'] for t in cleaned]
        sequence_string = ' → '.join(club_names)
        
        sequences.append({
            'player_id': player['player_id'],
            'player_name': player['player_name'],
            'market_value_numeric': player['market_value_numeric'],
            'num_moves': len(cleaned),
            'sequence_string': sequence_string,
            'clubs': cleaned
        })
    
    print(f"  ✓ Built {len(sequences)} sequences")
    if skipped > 0:
        print(f"  ⊘ Skipped {skipped} players (only youth/reserve clubs)")
    
    return sequences


def categorize_by_difficulty(sequences):
    """Categorize sequences by difficulty based on number of moves"""
    
    print("\nDifficulty Distribution (based on number of moves):")
    print("-"*80)
    
    from collections import Counter
    sequence_counts = Counter([s['sequence_string'] for s in sequences])
    
    for seq in sequences:
        seq['num_players_with_seq'] = sequence_counts[seq['sequence_string']]
        
        num_moves = seq['num_moves']
        
        if num_moves <= 4:
            difficulty = 'short'
        elif num_moves <= 7:
            difficulty = 'moderate'
        else:
            difficulty = 'long'
        
        seq['difficulty'] = difficulty
    
    difficulty_counts = {}
    for seq in sequences:
        diff = seq['difficulty']
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    for difficulty in ['short', 'moderate', 'long']:
        count = difficulty_counts.get(difficulty, 0)
        pct = count / len(sequences) * 100 if len(sequences) > 0 else 0
        bar = '█' * int(pct / 2)
        print(f"  {difficulty.capitalize():8s}: {count:4d} players ({pct:5.1f}%) {bar}")
    
    print("-"*80)
    
    return sequences


def store_difficulty_analysis(conn, sequences):
    """Store difficulty analysis in database"""
    
    print("\nStoring difficulty analysis...")
    
    conn.execute("DROP TABLE IF EXISTS sequence_analysis")
    
    conn.execute("""
        CREATE TABLE sequence_analysis (
            player_id VARCHAR PRIMARY KEY,
            player_name VARCHAR,
            market_value_numeric FLOAT,
            num_moves INTEGER,
            num_players_with_same_seq INTEGER,
            difficulty VARCHAR,
            sequence_string VARCHAR,
            club_jsons JSON
        )
    """)
    
    for seq in sequences:
        conn.execute("""
            INSERT INTO sequence_analysis
            (player_id, player_name, market_value_numeric, num_moves, num_players_with_same_seq, 
             difficulty, sequence_string, club_jsons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            seq['player_id'],
            seq['player_name'],
            seq['market_value_numeric'],
            seq['num_moves'],
            seq['num_players_with_seq'],
            seq['difficulty'],
            seq['sequence_string'],
            json.dumps(seq['clubs'])
        ])
    
    print("  ✓ Created sequence_analysis table")


def main():
    """Main execution"""
    print("="*80)
    print(" ANALYZE SEQUENCES (Cleaned)")
    print("="*80)
    print("\nCleaning rules:")
    print("  1. Exclude youth/reserve teams (U18, U21, etc.)")
    print("  2. Merge loan + permanent to same club")
    
    db_path = 'transfermarkt.db'
    conn = duckdb.connect(db_path)
    print(f"\n✓ Connected to {db_path}")
    
    tables = conn.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'transfer_details'
    """).fetchdf()
    
    if len(tables) == 0:
        print("\n Error: transfer_details table not found!")
        print("   Please run the transfer spider first.")
        return
    
    count = conn.execute("SELECT COUNT(*) FROM transfer_details").fetchone()[0]
    if count == 0:
        print("\n Error: transfer_details table is empty!")
        return
    
    print(f"  Found {count} transfer records")
    
    sequences = get_all_sequences(conn)
    
    if len(sequences) == 0:
        print("\n Error: No sequences could be built!")
        return
    
    sequences = categorize_by_difficulty(sequences)
    store_difficulty_analysis(conn, sequences)
    
    conn.close()
    
    print("\n" + "="*80)
    print("\nData preparation is complete!")
    print("="*80)

    print("You now have:")
    print("  - clubs table (with logos)")
    print("  - sequence_analysis table (with difficulty)")
    print("\nSequences are cleaned:")
    print("  ✓ No youth/reserve clubs")
    print("  ✓ Loan + permanent to same club merged")
    print("\nNext: Build the game interface!")


if __name__ == '__main__':
    main()