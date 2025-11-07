"""
Player lookup API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import PlayerLookupResponse
from app.services.game_service import GameService

router = APIRouter(prefix="/player", tags=["player"])


@router.get("/{player_name}", response_model=PlayerLookupResponse)
def lookup_player(player_name: str):
    """
    Lookup a player by name and return their career sequence
    
    Args:
        player_name: Player name (supports fuzzy matching)
        
    Returns:
        Player career sequence with clubs and metadata
        
    Raises:
        HTTPException: 404 if player not found (or match score too low)
    """
    try:
        return GameService.lookup_player(player_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error looking up player: {str(e)}")