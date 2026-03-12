#!/usr/bin/env python3
"""Create app icon for 反復 (Hanpuku) SRS application."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create an icon with the kanji 反復."""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw circular background with gradient effect (red/orange theme for SRS)
    # Outer circle - darker red
    margin = int(size * 0.05)
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill='#c0392b')

    # Inner circle - lighter red/coral
    inner_margin = int(size * 0.08)
    draw.ellipse([inner_margin, inner_margin, size - inner_margin, size - inner_margin],
                 fill='#e74c3c')

    # Try to find a Japanese font
    font_paths = [
        '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    ]

    font = None
    font_size = int(size * 0.35)

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue

    if font is None:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw the kanji 反復 (Hanpuku - repetition)
    text = "反復"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - int(size * 0.05)

    # Draw text shadow
    shadow_offset = max(1, int(size * 0.015))
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill='#922b21')

    # Draw main text in white
    draw.text((x, y), text, font=font, fill='white')

    # Add a small circular arrow at the bottom to represent repetition
    arrow_y = int(size * 0.75)
    arrow_size = int(size * 0.15)
    arrow_x = (size - arrow_size) // 2

    # Simple arc to represent cycling/repetition
    draw.arc([arrow_x, arrow_y - arrow_size//2, arrow_x + arrow_size, arrow_y + arrow_size//2],
             45, 315, fill='white', width=max(2, int(size * 0.03)))

    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created {output_path}")

def main():
    """Create icons in multiple sizes."""
    output_dir = '/Users/broganbunt/python_work/SRS/src/resources'

    # Create icons in different sizes
    sizes = [64, 128, 256, 512, 1024]

    for size in sizes:
        output_path = os.path.join(output_dir, f'icon_{size}.png')
        create_icon(size, output_path)

    print("All icons created successfully!")

if __name__ == '__main__':
    main()
