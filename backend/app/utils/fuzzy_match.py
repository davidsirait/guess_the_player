"""
Fuzzy matching utilities for player name matching
"""

from typing import Tuple, List
from rapidfuzz import fuzz, process


def fuzzy_match_player(query: str, candidates: List[str]) -> Tuple[str, int]:
    """
    Find the best fuzzy match for a query among candidates
    
    Args:
        query: Search query
        candidates: List of candidate strings to match against
        
    Returns:
        Tuple of (best_match, score)
        If no match found, returns (query, 0)
    """
    if not candidates:
        return query, 0
    
    best_match = process.extractOne(
        query,
        candidates,
        scorer=fuzz.ratio
    )
    
    if best_match:
        return best_match[0], best_match[1]
    
    return query, 0