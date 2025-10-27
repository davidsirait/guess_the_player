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
    
    # sanitize club name by lowercasing and remove whitespace
    club_clean = club_name.lower()
    club_clean = club_clean.strip()
    
    # Keywords to filter out
    youth_keywords = [
        'u17', 'u18', 'u19', 'u20', 'u21', 'u22', 'u23',
        'sub-15', 'sub-17', 'sub-19', 'sub-20', 'sub-21',
        'youth', 'reserve', 'reserves', 'yth.', 'yth', 'you.', 
        'b team', 'b-team', 'acad.', 'academy', 'ii',
        'ii team', 'ii-team', 'jgd.', 'jong', 'jrs.',
        'under 18', 'under 19', 'under 21', 'under 23',
        'u-18', 'u-19', 'u-21', 'u-23',
        'juvenil', 'juvenile',
    ]
    
    # check keywords
    if any(keyword in club_clean for keyword in youth_keywords):
        return True
    
    # check if the club ends with B, C, or D (example: "Real Madrid B")
    # e.g., "Barcelona B", "Real Madrid C", "Team D"
    if club_name.endswith(' B') or club_name.endswith(' C') or club_name.endswith(' D'):
        return True


def build_cleaned_sequence(transfers_list):
    """
    Build sequence with:
    1. No youth/reserve clubs
    2. Loan followed by permanent to same club = single entry
    3. Sequential loans from same parent club = hide parent club in between
    
    Example:
    Before: Man Utd → Preston (Loan) → Man Utd → Sunderland (Loan) → Man Utd → Arsenal
    After:  Man Utd → Preston → Sunderland → Man Utd → Arsenal
    """
    
    cleaned = []
    parent_club = None  # Track parent club during loan spells
    
    for i, transfer in enumerate(transfers_list):
        club = transfer['to_club']
        fee = transfer.get('fee', '')
        
        # Skip youth/reserve clubs
        if is_youth_or_reserve_club(club):
            continue
        
        is_loan = fee and 'loan' in fee.lower()
        print(f"Processing transfer to {club} | Fee: {fee} | Is loan: {is_loan}")
        
        # Determine if this is returning from loan
        is_return_from_loan = fee and 'end of loan' in fee.lower()
        
        if len(cleaned) > 0:
            prev = cleaned[-1]
            prev_was_loan = prev.get('is_loan', False)

            # If previous was loan and now returning to a club
            if prev_was_loan and is_return_from_loan:
                # Check if next transfer is also a loan
                # If yes, this return is just between loans - skip it
                if i + 1 < len(transfers_list):
                    next_transfer = transfers_list[i + 1]
                    next_fee = next_transfer.get('fee', '')
                    next_is_loan = next_fee and 'loan' in next_fee.lower()
                    print(f"Next transfer to {next_transfer.get('to_club')} | Fee: {fee} | Is loan: {next_is_loan}")
                    
                    # Skip this return if next is also loan
                    if next_is_loan:
                        parent_club = club  # Remember parent club
                        continue
        
        # Check if previous entry was a loan to this same club
        if len(cleaned) > 0:
            prev = cleaned[-1]
            prev_club = prev['club']
            prev_was_loan = prev.get('is_loan', False)
            
            # If prev was loan to same club, and now permanent move to same club
            # Replace the loan entry with permanent entry
            if prev_was_loan and prev_club == club and not is_loan:
                cleaned[-1] = {
                    'club': club,
                    'logo': transfer['to_club_image_url'],
                    'season': transfer['season'],
                    'fee': fee,
                    'is_loan': False
                }
                parent_club = None
                continue
        
        # Add this transfer
        cleaned.append({
            'club': club,
            'logo': transfer['to_club_image_url'],
            'season': transfer['season'],
            'fee': fee,
            'is_loan': is_loan
        })

        # Update parent club tracking
        if not is_loan:
            parent_club = club

    return cleaned


def get_all_sequences(conn):
    """Get all player sequences with cleaning applied"""
    
    print("\nBuilding cleaned sequences from transfer_details...")
    
    # Get all players
    players = conn.execute("""
        SELECT DISTINCT player_id, player_name
        FROM players
        WHERE player_name == 'Kylian Mbappe'
        -- ORDER BY player_name
    """).fetchdf()
    
    sequences = []
    skipped = 0
    
    for _, player in players.iterrows():
        # Get transfers for this player
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

        # Convert to list of dicts
        transfers_list = transfers.to_dict('records')
        
        # Build cleaned sequence
        cleaned = build_cleaned_sequence(transfers_list)
        
        if len(cleaned) == 0:
            skipped += 1
            continue
        
        # Build sequence string
        club_names = [t['club'] for t in cleaned]
        sequence_string = ' → '.join(club_names)
        
        sequences.append({
            'player_id': player['player_id'],
            'player_name': player['player_name'],
            'num_moves': len(cleaned),
            'sequence_string': sequence_string,
            'clubs': cleaned
        })
    
    print(f"  ✓ Built {len(sequences)} sequences")
    if skipped > 0:
        print(f"  ⊘ Skipped {skipped} players (only youth/reserve clubs)")
    
    return sequences


def analyze_sequence_uniqueness(sequences):
    """Find how many players share the same sequence"""
    
    print("\nAnalyzing Sequence Uniqueness (with cleaning applied)...")
    print("-"*80)
    
    # Count duplicates
    from collections import Counter
    sequence_counts = Counter([s['sequence_string'] for s in sequences])
    
    # Statistics
    total_players = len(sequences)
    unique_sequences = len([s for s, count in sequence_counts.items() if count == 1])
    duplicate_sequences = len([s for s, count in sequence_counts.items() if count > 1])
    print(f"Sample duplicate sequences: {[s for s, count in sequence_counts.items() if count == 1][-1]}")
    
    print(f"  Total players: {total_players}")
    print(f"  Unique sequences: {unique_sequences} ({unique_sequences/total_players*100:.1f}%)")
    print(f"  Shared sequences: {duplicate_sequences} ({duplicate_sequences/total_players*100:.1f}%)")
    
    # Average moves
    avg_moves = sum(s['num_moves'] for s in sequences) / len(sequences) if sequences else 0
    print(f"  Average moves per player: {avg_moves:.2f}")
    
    # Show most common sequences
    print("\n  Most common sequences (shared by multiple players):")
    most_common = sequence_counts.most_common(5)
    
    for seq, count in most_common:
        if count > 1:
            print(f"    [{count} players] {seq[:80]}{'...' if len(seq) > 80 else ''}")
            
            # Show which players
            players_with_seq = [s['player_name'] for s in sequences if s['sequence_string'] == seq]
            print(f"      Players: {', '.join(players_with_seq[:3])}")
            if len(players_with_seq) > 3:
                print(f"      ... and {len(players_with_seq) - 3} more")
    
    print("-"*80)
    
    return sequence_counts


def categorize_by_difficulty(sequences):
    """Categorize sequences by difficulty (based on length and uniqueness)"""
    
    print("\nDifficulty Distribution (based on number of moves):")
    print("-"*80)
    
    # Count sequence occurrences
    from collections import Counter
    sequence_counts = Counter([s['sequence_string'] for s in sequences])
    
    # Add uniqueness info and difficulty
    for seq in sequences:
        seq['num_players_with_seq'] = sequence_counts[seq['sequence_string']]
        
        # Categorize difficulty
        num_moves = seq['num_moves']
        num_players = seq['num_players_with_seq']
        
        # Easy: Short career (2-4 moves) AND unique or rare
        if num_moves <= 4 :
            difficulty = 'easy'
        # Medium: 5-8 moves OR somewhat shared
        elif num_moves <= 8 :
            difficulty = 'medium'
        # Hard: Long career (9+ moves) OR very common sequence
        else :
            difficulty = 'hard'
        
        seq['difficulty'] = difficulty
    
    # Show distribution
    difficulty_counts = {}
    for seq in sequences:
        diff = seq['difficulty']
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    for difficulty in ['easy', 'medium', 'hard']:
        count = difficulty_counts.get(difficulty, 0)
        pct = count / len(sequences) * 100 if len(sequences) > 0 else 0
        bar = '█' * int(pct / 2)
        print(f"  {difficulty.capitalize():8s}: {count:4d} players ({pct:5.1f}%) {bar}")
    
    print("-"*80)
    
    return sequences


def store_difficulty_analysis(conn, sequences):
    """Store difficulty analysis in database"""
    
    print("\nStoring difficulty analysis...")
    
    # Create analysis table
    conn.execute("DROP TABLE IF EXISTS sequence_analysis")
    
    conn.execute("""
        CREATE TABLE sequence_analysis (
            player_id VARCHAR PRIMARY KEY,
            player_name VARCHAR,
            num_moves INTEGER,
            num_players_with_same_seq INTEGER,
            difficulty VARCHAR,
            sequence_string VARCHAR,
            club_jsons JSON
        )
    """)
    
    # Insert data
    for seq in sequences:
        conn.execute("""
            INSERT INTO sequence_analysis
            (player_id, player_name, num_moves, num_players_with_same_seq, 
             difficulty, sequence_string, club_jsons)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            seq['player_id'],
            seq['player_name'],
            seq['num_moves'],
            seq['num_players_with_seq'],
            seq['difficulty'],
            seq['sequence_string'],
            json.dumps(seq['clubs'])
        ])
    
    print("  ✓ Created sequence_analysis table")


def show_sample_questions(sequences):
    """Show sample game questions by difficulty"""
    
    print("\nSample Game Questions:")
    print("="*80)
    
    import random
    
    for difficulty in ['easy', 'medium', 'hard']:
        print(f"\n{difficulty.upper()} Questions:")
        print("-"*80)
        
        # Get samples
        samples = [s for s in sequences if s['difficulty'] == difficulty]
        
        if len(samples) == 0:
            print(f"  No {difficulty} questions available")
            continue
        
        # Show 3 random samples
        for sample in random.sample(samples, min(3, len(samples))):
            seq_display = sample['sequence_string'][:100] + '...' if len(sample['sequence_string']) > 100 else sample['sequence_string']
            print(f"\nSequence: {seq_display}")
            print(f"Answer: {sample['player_name']}")
            print(f"Moves: {sample['num_moves']} | Shared by: {sample['num_players_with_seq']} player(s)")
    
    print("\n" + "="*80)


def find_interesting_sequences(sequences):
    """Find interesting sequences for special challenges"""
    
    print("\nInteresting Sequences:")
    print("-"*80)
    
    # Sort by num_moves
    sorted_by_moves = sorted(sequences, key=lambda x: x['num_moves'], reverse=True)
    
    # Longest careers
    print("\n1. Longest Careers (most moves):")
    for seq in sorted_by_moves[:5]:
        print(f"  {seq['player_name']}: {seq['num_moves']} moves")
        seq_display = seq['sequence_string'][:120] + '...' if len(seq['sequence_string']) > 120 else seq['sequence_string']
        print(f"    {seq_display}")
    
    # Shortest careers
    print("\n2. Shortest Careers (fewest moves):")
    shortest = sorted([s for s in sequences if s['num_moves'] >= 2], key=lambda x: x['num_moves'])
    for seq in shortest[:5]:
        print(f"  {seq['player_name']}: {seq['num_moves']} moves")
        print(f"    {seq['sequence_string']}")
    
    # Most unique
    print("\n3. Most Unique Long Careers:")
    unique_long = sorted(
        [s for s in sequences if s['num_players_with_seq'] == 1 and s['num_moves'] >= 6],
        key=lambda x: x['num_moves'],
        reverse=True
    )
    
    if len(unique_long) > 0:
        for seq in unique_long[:5]:
            print(f"  {seq['player_name']}: {seq['num_moves']} moves (unique path!)")
            seq_display = seq['sequence_string'][:100] + '...' if len(seq['sequence_string']) > 100 else seq['sequence_string']
            print(f"    {seq_display}")
    else:
        print("  No unique long careers found")
    
    print("-"*80)


def export_game_ready_data(sequences):
    """Export data ready for game use"""
    
    print("\nExporting game-ready data...")
    
    import random
    
    # Export by difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        # Get sequences for this difficulty
        diff_sequences = [s for s in sequences if s['difficulty'] == difficulty]
        
        if len(diff_sequences) == 0:
            print(f"  ⚠️  No {difficulty} questions available")
            continue
        
        # Sample up to 100
        sample_size = min(100, len(diff_sequences))
        sampled = random.sample(diff_sequences, sample_size)
        
        # Prepare game data
        game_data = []
        for seq in sampled:
            game_data.append({
                'player_id': seq['player_id'],
                'player_name': seq['player_name'],
                'difficulty': seq['difficulty'],
                'num_moves': seq['num_moves'],
                'shared_by': seq['num_players_with_seq'],
                'clubs': [
                    {
                        'club_name': club['club'],
                        'club_logo_url': club['logo'],
                        'season': club['season'],
                        'fee': club['fee']
                    }
                    for club in seq['clubs']
                ]
            })
        
        # Save to JSON
        output_file = f'./output/game_data_{difficulty}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Exported {len(game_data)} {difficulty} questions to {output_file}")


def show_move_distribution(sequences):
    """Show distribution of moves per player"""
    
    print("\nMove Distribution (cleaned sequences):")
    print("-"*80)
    
    from collections import Counter
    move_counts = Counter([s['num_moves'] for s in sequences])
    
    for num_moves in sorted(move_counts.keys())[:15]:
        count = move_counts[num_moves]
        bar = '█' * int(count / 10) if count >= 10 else '▌'
        print(f"  {num_moves:2d} moves: {count:4d} players {bar}")
    
    print("-"*80)


def main():
    """Main execution"""
    print("="*80)
    print(" ANALYZE SEQUENCES (Cleaned)")
    print("="*80)
    print("\nCleaning rules:")
    print("  1. Exclude youth/reserve teams (U18, U21, etc.)")
    print("  2. Merge loan + permanent to same club")
    
    # Connect to database
    db_path = 'transfermarkt.db'
    conn = duckdb.connect(db_path)
    print(f"\n✓ Connected to {db_path}")
    
    # Check prerequisites
    tables = conn.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'transfer_details'
    """).fetchdf()
    
    if len(tables) == 0:
        print("\n❌ Error: transfer_details table not found!")
        print("   Please run the transfer spider first.")
        return
    
    # Check if table has data
    count = conn.execute("SELECT COUNT(*) FROM transfer_details").fetchone()[0]
    if count == 0:
        print("\n❌ Error: transfer_details table is empty!")
        return
    
    print(f"  Found {count} transfer records")
    
    # Build sequences (with cleaning)
    sequences = get_all_sequences(conn)
    
    if len(sequences) == 0:
        print("\n❌ Error: No sequences could be built!")
        return
    
    # Run analyses
    # analyze_sequence_uniqueness(sequences)
    sequences = categorize_by_difficulty(sequences)
    # show_move_distribution(sequences)
    # store_difficulty_analysis(conn, sequences)
    # show_sample_questions(sequences)
    find_interesting_sequences(sequences)
    # export_game_ready_data(sequences)
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ STEP 3 COMPLETED!")
    print("="*80)
    print("\nData preparation is complete!")
    print("You now have:")
    print("  - clubs table (with logos)")
    print("  - sequence_analysis table (with difficulty)")
    print("  - game_data_*.json files (ready to use)")
    print("\nSequences are cleaned:")
    print("  ✓ No youth/reserve clubs")
    print("  ✓ Loan + permanent to same club merged")
    print("\nNext: Build the game interface!")


if __name__ == '__main__':
    main()