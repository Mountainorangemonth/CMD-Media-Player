import os
from PIL import Image
import time
import colorsys

# --- Config ---
ASCII_CHARS = "`.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"

def get_terminal_size():
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24

def rgb_to_ansi(r, g, b):
    return f'\x1b[38;2;{r};{g};{b}m'

def resize_image(img):
    """Resizes the image to fit the terminal width, returns the new image and dimensions."""
    terminal_width, _ = get_terminal_size()
    new_width = min(terminal_width, 250)
    width, height = img.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width * 0.55)
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS), new_width, new_height

# --- Classic Mode --- #
def image_to_classic_ascii(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return f"Error: {e}"

    img, new_width, _ = resize_image(img)
    pixels = img.getdata()
    
    art = []
    for i, p in enumerate(pixels):
        r, g, b = p
        brightness = sum(p) / 3
        char_index = int((brightness / 255) * (len(ASCII_CHARS) - 1))
        char = ASCII_CHARS[char_index]
        color_code = rgb_to_ansi(r, g, b)
        art.append(f"{color_code}{char}")
        if (i + 1) % new_width == 0:
            art.append("\n")
    art.append("\x1b[0m")
    return "".join(art)

# --- Rainbow Mode --- #
def image_to_rainbow_ascii(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return f"Error: {e}"

    img, new_width, new_height = resize_image(img)
    pixels = img.getdata()
    
    art = []
    for i, p in enumerate(pixels):
        # Character is still based on the image's brightness
        brightness = sum(p) / 3
        char_index = int((brightness / 255) * (len(ASCII_CHARS) - 1))
        char = ASCII_CHARS[char_index]
        
        # But color is based on the character's position (x, y)
        x = i % new_width
        y = i // new_width
        
        # Create a flowing rainbow hue based on position
        hue = (x / new_width + y / new_height) / 2 % 1.0
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        
        color_code = rgb_to_ansi(r, g, b)
        art.append(f"{color_code}{char}")
        if (i + 1) % new_width == 0:
            art.append("\n")
    art.append("\x1b[0m")
    return "".join(art)

def main():
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
    except NameError:
        script_dir = os.getcwd()
    media_dir = os.path.join(script_dir, "media")

    if not os.path.exists(media_dir) or not os.listdir(media_dir):
        os.makedirs(media_dir, exist_ok=True)
        print(f"The '{os.path.basename(media_dir)}' directory is empty. Please add images.")
        return

    image_files = [f for f in os.listdir(media_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    if not image_files:
        print(f"No supported images found in '{os.path.basename(media_dir)}'.")
        return

    # --- Mode Selection ---
    print("Please select a rendering mode:")
    print("  1: Classic Color (image's original colors)")
    print("  2: Rainbow Glow (colors based on position)")
    try:
        mode_choice = input("Enter mode (1 or 2): ")
        if mode_choice not in ['1', '2']:
            print("Invalid mode. Exiting.")
            return
    except (ValueError, EOFError):
        print("\nInvalid input. Exiting.")
        return

    # --- File Selection ---
    print(f"\nFound images in '{os.path.basename(media_dir)}':")
    for i, f in enumerate(image_files):
        print(f"  {i+1}: {f}")
    try:
        choice_str = input(f"Enter the number of the image to convert (1-{len(image_files)}): ")
        file_choice = int(choice_str) - 1
        if not 0 <= file_choice < len(image_files):
            print("Invalid number.")
            return
    except (ValueError, EOFError):
        print("\nInvalid input. Exiting.")
        return

    selected_file = os.path.join(media_dir, image_files[file_choice])
    print("\nConverting your image...\n")

    # --- Render based on mode ---
    if mode_choice == '1':
        print(image_to_classic_ascii(selected_file))
    else:
        print(image_to_rainbow_ascii(selected_file))

if __name__ == "__main__":
    main()
