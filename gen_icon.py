import sys
import os

# Get the path to the user's Downloads folder
downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
icon_path = os.path.join(downloads_path, "shareme_icon.ico")

def create_placeholder_icon():
    from PIL import Image, ImageDraw
    # Create a simple high-res icon
    size = (256, 256)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Purple Circle
    draw.ellipse((10, 10, 246, 246), fill="#6366F1")
    # White Cloud-ish/File shape
    draw.rounded_rectangle((60, 80, 196, 176), radius=20, fill="white")
    draw.polygon([(110, 160), (146, 160), (128, 190)], fill="white") # Arrow/Pointer
    
    # Save as ICO with multiple sizes for Windows compatibility
    image.save(icon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icon created at: {icon_path}")

try:
    create_placeholder_icon()
except Exception as e:
    print(f"Failed to create icon: {e}")
