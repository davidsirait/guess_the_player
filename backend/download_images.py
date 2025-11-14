#!/usr/bin/env python3
"""
Download player images and club logos from external URLs
and save them locally for reliable serving
"""

import duckdb
import requests
import os
import time
from pathlib import Path
from PIL import Image
from io import BytesIO

# Directories
PLAYER_DIR = "static/images/players"
CLUB_DIR = "static/images/clubs"

# Create directories
os.makedirs(PLAYER_DIR, exist_ok=True)
os.makedirs(CLUB_DIR, exist_ok=True)


def download_image(url: str, save_path: str, timeout: int = 10) -> bool:
    """
    Download an image from URL and save it locally
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Open image with PIL to validate and convert if needed
        img = Image.open(BytesIO(response.content))
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        
        # Save as JPEG for players, PNG for clubs
        if save_path.endswith('.jpg'):
            img.save(save_path, 'JPEG', quality=85)
        else:
            img.save(save_path, 'PNG')
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {url}: {e}")
        return False


def download_player_images(db_path: str = "transfermarkt.db", limit: int = None):
    """Download player images from database"""
    print("\n" + "="*60)
    print("  Downloading Player Images")
    print("="*60)
    
    conn = duckdb.connect(db_path)
    
    # Get players with image URLs
    query = """
        SELECT player_id, player_name, player_img_url
        FROM players
        WHERE player_img_url IS NOT NULL
        AND player_img_url != ''
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    players = conn.execute(query).fetchall()
    conn.close()
    
    print(f"\nFound {len(players)} players with images")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for i, (player_id, player_name, img_url) in enumerate(players, 1):
        # Check if already exists
        save_path = f"{PLAYER_DIR}/{player_id}.jpg"
        if os.path.exists(save_path):
            skipped += 1
            continue
        
        print(f"[{i}/{len(players)}] Downloading {player_name}...", end=" ")
        
        if download_image(img_url, save_path):
            downloaded += 1
            print("✓")
        else:
            failed += 1
            print("✗")
        
        # Rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    print(f"\n✓ Downloaded: {downloaded}")
    print(f"⊘ Skipped (already exists): {skipped}")
    print(f"✗ Failed: {failed}")


def download_club_logos(db_path: str = "transfermarkt.db", limit: int = None):
    """Download club logos from database"""
    print("\n" + "="*60)
    print("  Downloading Club Logos")
    print("="*60)
    
    conn = duckdb.connect(db_path)
    
    # Get clubs with logo URLs
    query = """
        SELECT club_id, club_name, logo_url
        FROM clubs
        WHERE logo_url IS NOT NULL
        AND logo_url != ''
        AND logo_url NOT LIKE '%default%'
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    clubs = conn.execute(query).fetchall()
    conn.close()
    
    print(f"\nFound {len(clubs)} clubs with logos")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for i, (club_id, club_name, logo_url) in enumerate(clubs, 1):
        # Check if already exists
        save_path = f"{CLUB_DIR}/{club_id}.png"
        if os.path.exists(save_path):
            skipped += 1
            continue
        
        print(f"[{i}/{len(clubs)}] Downloading {club_name}...", end=" ")
        
        if download_image(logo_url, save_path):
            downloaded += 1
            print("✓")
        else:
            failed += 1
            print("✗")
        
        # Rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    print(f"\n✓ Downloaded: {downloaded}")
    print(f"⊘ Skipped (already exists): {skipped}")
    print(f"✗ Failed: {failed}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download images from database")
    parser.add_argument("--db", default="transfermarkt.db", help="Database path")
    parser.add_argument("--limit", type=int, help="Limit number of images to download (for testing)")
    parser.add_argument("--players-only", action="store_true", help="Only download player images")
    parser.add_argument("--clubs-only", action="store_true", help="Only download club logos")
    
    args = parser.parse_args()
    
    print("="*60)
    print("  Image Downloader")
    print("="*60)
    
    if not os.path.exists(args.db):
        print(f"\n✗ Error: Database not found: {args.db}")
        return
    
    if args.limit:
        print(f"\n⚠ Limit set to {args.limit} images (testing mode)")
    
    if not args.clubs_only:
        download_player_images(args.db, args.limit)
    
    if not args.players_only:
        download_club_logos(args.db, args.limit)
    
    print("\n" + "="*60)
    print("  Download Complete!")
    print("="*60)
    print(f"\nImages saved to:")
    print(f"  - {PLAYER_DIR}/")
    print(f"  - {CLUB_DIR}/")


if __name__ == "__main__":
    main()