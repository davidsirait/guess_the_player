"""
Image handling utilities with fallback support
"""

import os
from typing import Optional

# Base paths for images
STATIC_BASE = "/static/images"
PLAYER_IMAGE_DIR = "static/images/players"
CLUB_IMAGE_DIR = "static/images/clubs"

# Placeholder images
PLACEHOLDER_PLAYER = f"{STATIC_BASE}/placeholders/default-player.png"
PLACEHOLDER_CLUB = f"{STATIC_BASE}/placeholders/default-club.png"


def get_player_image_url(player_id: str, external_url: Optional[str] = None) -> str:
    """
    Get player image URL with fallback logic
    
    Priority:
    1. Local image if exists (downloaded)
    2. External URL if provided and valid
    3. Placeholder image
    
    Args:
        player_id: Player ID
        external_url: External image URL (from transfermarkt)
        
    Returns:
        Image URL to use
    """
    # Check if local image exists
    local_path = f"{PLAYER_IMAGE_DIR}/{player_id}.jpg"
    if os.path.exists(local_path):
        return f"{STATIC_BASE}/players/{player_id}.jpg"
    
    # Use external URL if valid
    if external_url and external_url.startswith('http'):
        return external_url
    
    # Fallback to placeholder
    return PLACEHOLDER_PLAYER


def get_club_image_url(club_id: str, external_url: Optional[str] = None) -> str:
    """
    Get club logo URL with fallback logic
    
    Priority:
    1. Local image if exists (downloaded)
    2. External URL if provided and valid
    3. Placeholder image
    
    Args:
        club_id: Club ID
        external_url: External logo URL (from transfermarkt)
        
    Returns:
        Image URL to use
    """
    # Check if local image exists
    local_path = f"{CLUB_IMAGE_DIR}/{club_id}.png"
    if os.path.exists(local_path):
        return f"{STATIC_BASE}/clubs/{club_id}.png"
    
    # Use external URL if valid
    if external_url and external_url.startswith('http'):
        return external_url
    
    # Fallback to placeholder
    return PLACEHOLDER_CLUB


def extract_player_id_from_url(url: str) -> Optional[str]:
    """Extract player ID from transfermarkt image URL"""
    try:
        # URL format: .../portrait/header/PLAYER_ID-timestamp.jpg
        parts = url.split('/')
        filename = parts[-1]
        player_id = filename.split('-')[0]
        return player_id
    except:
        return None


def extract_club_id_from_url(url: str) -> Optional[str]:
    """Extract club ID from transfermarkt image URL"""
    try:
        # URL format: .../wappen/head/CLUB_ID.png or CLUB_ID_timestamp.png
        parts = url.split('/')
        filename = parts[-1]
        club_id = filename.split('.')[0].split('_')[0]
        return club_id
    except:
        return None