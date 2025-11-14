#!/usr/bin/env python3
"""
Generate placeholder images for players and clubs
Run this once to create default fallback images
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create directories
os.makedirs("static/images/placeholders", exist_ok=True)

def create_player_placeholder():
    """Create a default player placeholder image"""
    # Create 200x200 image with gray background
    img = Image.new('RGB', (200, 200), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple person silhouette (circle head + shoulders)
    # Head
    draw.ellipse([70, 40, 130, 100], fill='#cccccc', outline='#999999', width=2)
    
    # Shoulders
    draw.arc([40, 90, 160, 180], start=180, end=0, fill='#cccccc', width=50)
    
    # Add text
    try:
        # Try to use a nice font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        # Fallback to default
        font = ImageFont.load_default()
    
    text = "No Image"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (200 - text_width) // 2
    y = 165
    
    draw.text((x, y), text, fill='#666666', font=font)
    
    # Save
    img.save("static/images/placeholders/default-player.png")
    print("✓ Created default-player.png")


def create_club_placeholder():
    """Create a default club logo placeholder image"""
    # Create 120x120 image with white background
    img = Image.new('RGB', (120, 120), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple shield shape
    points = [
        (60, 20),   # Top center
        (20, 40),   # Left top
        (20, 80),   # Left bottom
        (60, 105),  # Bottom center point
        (100, 80),  # Right bottom
        (100, 40)   # Right top
    ]
    draw.polygon(points, fill='#e8e8e8', outline='#aaaaaa')
    
    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    text = "NO\nLOGO"
    
    # Draw text with newline
    lines = text.split('\n')
    y_offset = 45
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (120 - text_width) // 2
        draw.text((x, y_offset), line, fill='#888888', font=font)
        y_offset += 20
    
    # Save
    img.save("static/images/placeholders/default-club.png")
    print("✓ Created default-club.png")


def main():
    print("="*60)
    print("  Creating Placeholder Images")
    print("="*60)
    
    print("\nGenerating images...")
    create_player_placeholder()
    create_club_placeholder()
    
    print("\n" + "="*60)
    print("  Done! Placeholder images created in:")
    print("  static/images/placeholders/")
    print("="*60)


if __name__ == "__main__":
    main()