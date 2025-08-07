import os
from PIL import Image
import time
import cv2
import sys
import sys

# --- 配置 ---
ASCII_CHARS = "`.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
CHAR_ASPECT_RATIO = 0.55 # 终端中单个字符的高/宽比

# --- 终端与图像处理核心函数 ---
def get_terminal_size():
    try:
        return os.get_terminal_size().columns, os.get_terminal_size().lines - 1
    except OSError:
        return 80, 23

def rgb_to_ansi(r, g, b):
    return f'\x1b[38;2;{r};{g};{b}m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- 纯Python图像转换引擎 (最终“优先宽度”缩放算法) ---
def image_to_ascii(pil_image):
    """使用纯Python将PIL图像转换为ASCII艺术，优先填满宽度，除非高度超限。"""
    term_w, term_h = get_terminal_size()
    if term_w < 1 or term_h < 1: return ""

    img_w, img_h = pil_image.size
    img_aspect = img_h / img_w

    # --- 最终的、正确的“优先宽度”算法 ---
    # 1. 首先，大胆地以终端宽度为基准计算高度
    new_width = term_w
    new_height = int(new_width * img_aspect * CHAR_ASPECT_RATIO)

    # 2. 然后，检查计算出的高度是否超出了终端的限制
    if new_height > term_h:
        # 如果高度超限，则证明图片太“高”了，必须反过来以高度为基准进行缩放
        new_height = term_h
        new_width = int(new_height / img_aspect / CHAR_ASPECT_RATIO)

    if new_width < 1 or new_height < 1: return ""

    img = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img = img.convert("RGB")

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

# --- 视频播放逻辑 ---
def play_video_ascii(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("错误：无法打开视频文件。")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps if fps > 0 else 1 / 30

    print("即将开始播放... 按 Ctrl+C 停止播放。")
    time.sleep(1)

    try:
        while True:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret: break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)
            ascii_art = image_to_ascii(pil_frame)
            
            back_buffer = ['\x1b[H', ascii_art]
            sys.stdout.write("".join(back_buffer))
            sys.stdout.flush()

            render_time = time.time() - start_time
            sleep_time = frame_duration - render_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n播放已被用户停止。")
    finally:
        cap.release()
        clear_screen()
        print("\x1b[0m")

# --- 主程序 ---
def main():
    if getattr(sys, 'frozen', False):
        # If run as a bundle, the executable's path is in sys.executable
        script_dir = os.path.dirname(sys.executable)
    else:
        # If run as a script, use the script's path
        script_dir = os.path.dirname(os.path.realpath(__file__))
    media_dir = os.path.join(script_dir, "media")

    if not os.path.exists(media_dir) or not os.listdir(media_dir):
        os.makedirs(media_dir, exist_ok=True)
        print(f"'{os.path.basename(media_dir)}' 文件夹是空的，请在其中放入媒体文件。")
        return

    files = os.listdir(media_dir)
    image_exts = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    video_exts = ['.mp4', '.mkv', '.avi', '.mov']
    media_files = [f for f in files if f.lower().endswith(tuple(image_exts + video_exts))]
    if not media_files:
        print(f"在 '{os.path.basename(media_dir)}' 文件夹中未找到支持的媒体文件。")
        return

    print(f"在 '{os.path.basename(media_dir)}' 文件夹中找到以下文件：")
    for i, f in enumerate(media_files):
        print(f"  {i+1}: {f}")

    try:
        choice_str = input(f"\n请输入你想播放的文件的序号 (1-{len(media_files)}): ")
        choice = int(choice_str) - 1
        if not 0 <= choice < len(media_files):
            print("无效的序号。")
            return
    except (ValueError, EOFError):
        print("\n输入无效，程序退出。")
        return

    selected_file = os.path.join(media_dir, media_files[choice])
    _, extension = os.path.splitext(selected_file)

    if extension.lower() in image_exts:
        try:
            img = Image.open(selected_file)
            clear_screen()
            print(image_to_ascii(img))
            input("\n图片显示完毕。按回车键返回菜单...")
            clear_screen()
        except Exception as e:
            print(f"处理图片时出错: {e}")
    elif extension.lower() in video_exts:
        play_video_ascii(selected_file)

if __name__ == "__main__":
    main()