import os
import sys
import time
import tempfile
import subprocess
import shutil
import colorsys
import threading
import queue
from PIL import Image
import cv2

# =========================== 用户可配置项 ===========================
ASCII_CHARS = " *"
CHAR_ASPECT_RATIO = 0.65
MAX_FPS = 120                # 锁定120帧
COLOR_MODE = 'classic'      # 'classic' 或 'rainbow'
ADAPTIVE_ENABLED = False     # 关闭自适应
# ==================================================================

frame_queue = queue.Queue(maxsize=2)
ascii_queue = queue.Queue(maxsize=2)
stop_threads = False

def get_terminal_size():
    try:
        return os.get_terminal_size().columns, os.get_terminal_size().lines - 1
    except OSError:
        return 80, 23

def rgb_to_ansi(r, g, b):
    return f'\x1b[38;2;{r};{g};{b}m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_ffmpeg_path(executable_name):
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        local_path = os.path.join(base_dir, executable_name)
        if os.path.exists(local_path):
            return local_path
        if hasattr(sys, '_MEIPASS'):
            meipass_path = os.path.join(sys._MEIPASS, executable_name)
            if os.path.exists(meipass_path):
                return meipass_path
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(base_dir, executable_name)
        if os.path.exists(local_path):
            return local_path
    return shutil.which(executable_name) or executable_name

def image_to_ascii(pil_image):
    term_w, term_h = get_terminal_size()
    if term_w < 1 or term_h < 1:
        return ""

    img_w, img_h = pil_image.size
    img_aspect = img_h / img_w

    new_width = term_w
    new_height = int(new_width * img_aspect * CHAR_ASPECT_RATIO)
    if new_height > term_h:
        new_height = term_h
        new_width = int(new_height / img_aspect / CHAR_ASPECT_RATIO)

    new_width = max(1, new_width)
    new_height = max(1, new_height)

    # LANCZOS 高质量缩放（如果卡顿可改为 NEAREST）
    img = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img = img.convert("RGB")
    pixels = img.getdata()

    offset_x = (term_w - new_width) // 2
    offset_y = (term_h - new_height) // 2

    lines = []
    for y in range(term_h):
        if y < offset_y or y >= offset_y + new_height:
            lines.append(" " * term_w)
        else:
            line_chars = []
            for x in range(term_w):
                if x < offset_x or x >= offset_x + new_width:
                    line_chars.append(" ")
                else:
                    idx = (y - offset_y) * new_width + (x - offset_x)
                    r, g, b = pixels[idx]
                    brightness = sum((r, g, b)) / 3
                    char_index = int((brightness / 255) * (len(ASCII_CHARS) - 1))
                    char = ASCII_CHARS[char_index]
                    if COLOR_MODE == 'rainbow':
                        hue = (x / term_w + y / term_h) / 2 % 1.0
                        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    line_chars.append(f"{rgb_to_ansi(r, g, b)}{char}")
            lines.append("".join(line_chars))
    lines.append("\x1b[0m")
    return "\n".join(lines)

# ---------- 多线程函数 ----------
def reader_thread(video_path):
    global stop_threads
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("错误：无法打开视频文件。")
        stop_threads = True
        return
    try:
        while not stop_threads:
            ret, frame = cap.read()
            if not ret:
                break
            try:
                frame_queue.put(frame, timeout=0.5)
            except queue.Full:
                pass
    finally:
        cap.release()
        frame_queue.put(None)

def processor_thread():
    global stop_threads
    while not stop_threads:
        try:
            frame = frame_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if frame is None:
            ascii_queue.put(None)
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_frame = Image.fromarray(frame_rgb)
        ascii_art = image_to_ascii(pil_frame)
        ascii_queue.put(ascii_art)

# ---------- 音频处理 ----------
def extract_audio_ffmpeg(video_path, output_path):
    ffmpeg_path = get_ffmpeg_path('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
    if ffmpeg_path is None or not os.path.exists(ffmpeg_path):
        print("错误：未找到 ffmpeg。")
        return False
    cmd = [ffmpeg_path, '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-y', output_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=60)
        if proc.returncode != 0:
            print("ffmpeg 提取音频失败，错误信息：")
            print(proc.stderr)
            return False
        return True
    except Exception as e:
        print(f"ffmpeg 运行异常: {e}")
        return False

def play_audio_ffplay(audio_path):
    ffplay_path = get_ffmpeg_path('ffplay.exe' if os.name == 'nt' else 'ffplay')
    if ffplay_path is None or not os.path.exists(ffplay_path):
        print("错误：未找到 ffplay。")
        return None
    cmd = [ffplay_path, '-autoexit', '-loglevel', 'error', '-left', '9999', '-top', '9999', '-window_title', 'Audio', audio_path]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        return proc
    except Exception as e:
        print(f"启动 ffplay 失败: {e}")
        return None

def auto_fullscreen():
    try:
        import pyautogui
        pyautogui.press('f11')
        print("✓ 已自动全屏。")
    except:
        print(" 请手动按 F11 全屏。")

def play_video_ascii(video_path):
    global stop_threads
    auto_fullscreen()
    audio_proc = None
    audio_temp = None

    audio_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio_temp.close()
    print("正在提取音频（使用 ffmpeg）...")
    if extract_audio_ffmpeg(video_path, audio_temp.name):
        print("音频提取成功，启动 ffplay（窗口已隐藏）...")
        audio_proc = play_audio_ffplay(audio_temp.name)
        if audio_proc is None:
            print("警告：ffplay 启动失败，继续播放画面。")
        else:
            print("ffplay 已启动。")
    else:
        print("音频提取失败，继续播放画面。")
        audio_temp = None

    cap_test = cv2.VideoCapture(video_path)
    if not cap_test.isOpened():
        print("错误：无法打开视频文件。")
        return
    original_fps = cap_test.get(cv2.CAP_PROP_FPS)
    if original_fps <= 0:
        original_fps = 30
    # 目标帧率取原始帧率和 MAX_FPS 的较小值
    target_fps = min(original_fps, MAX_FPS)
    frame_duration = 1.0 / target_fps
    total_frames = int(cap_test.get(cv2.CAP_PROP_FRAME_COUNT))
    cap_test.release()
    print(f"原始帧率: {original_fps:.2f} FPS，目标帧率: {target_fps:.2f} FPS，总帧数: {total_frames}")
    print("按 Ctrl+C 停止播放。")
    print(f"颜色模式: {COLOR_MODE}")

    # 启动线程
    stop_threads = False
    while not frame_queue.empty():
        try: frame_queue.get_nowait()
        except: break
    while not ascii_queue.empty():
        try: ascii_queue.get_nowait()
        except: break

    reader = threading.Thread(target=reader_thread, args=(video_path,))
    processor = threading.Thread(target=processor_thread)
    reader.daemon = True
    processor.daemon = True
    reader.start()
    processor.start()

    start_time = time.time()
    frame_index = 0

    try:
        while not stop_threads:
            try:
                ascii_art = ascii_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if ascii_art is None:
                break
            sys.stdout.write('\x1b[H' + ascii_art)
            sys.stdout.flush()

            # 帧率控制：若落后超过一帧，则跳过（不额外等待）
            expected_time = start_time + frame_index * frame_duration
            current_time = time.time()
            sleep_time = expected_time - current_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            # 如果落后，不处理，直接下一帧（但已经显示了当前帧，可能会略快，但不会累积）
            frame_index += 1

    except KeyboardInterrupt:
        print("\n播放停止。")
    finally:
        stop_threads = True
        reader.join(timeout=1)
        processor.join(timeout=1)
        if audio_proc is not None:
            if audio_proc.poll() is None:
                audio_proc.terminate()
                time.sleep(0.3)
                if audio_proc.poll() is None:
                    audio_proc.kill()
            try:
                stdout, stderr = audio_proc.communicate(timeout=1)
                if stderr:
                    print("ffplay 错误:", stderr)
            except:
                pass
        if audio_temp and os.path.exists(audio_temp.name):
            try:
                os.unlink(audio_temp.name)
                print("临时音频文件已删除。")
            except:
                pass
        clear_screen()
        print("\x1b[0m")

# ---------- 图片显示 ----------
def display_image(file_path):
    try:
        img = Image.open(file_path)
        clear_screen()
        print(image_to_ascii(img))
        input("\n按回车返回...")
        clear_screen()
    except Exception as e:
        print(f"图片错误: {e}")

# ---------- 文件选择 ----------
def select_and_process_file(media_dir):
    if not os.path.exists(media_dir) or not os.listdir(media_dir):
        print(f"'{os.path.basename(media_dir)}' 为空。")
        return
    files = os.listdir(media_dir)
    image_exts = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    video_exts = ['.mp4', '.mkv', '.avi', '.mov']
    media_files = [f for f in files if f.lower().endswith(tuple(image_exts + video_exts))]
    if not media_files:
        print("没有支持的媒体文件。")
        return
    print("找到以下文件：")
    for i, f in enumerate(media_files):
        print(f"  {i+1}: {f}")
    try:
        choice = int(input(f"\n请输入序号 (1-{len(media_files)}): ")) - 1
        if not 0 <= choice < len(media_files):
            print("序号无效。")
            return
    except:
        print("输入无效。")
        return
    selected_file = os.path.join(media_dir, media_files[choice])
    _, ext = os.path.splitext(selected_file)
    if ext.lower() in image_exts:
        display_image(selected_file)
    elif ext.lower() in video_exts:
        play_video_ascii(selected_file)

# ---------- 主菜单 ----------
def main():
    global COLOR_MODE

    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(script_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    while True:
        clear_screen()
        print("=== CMD-Media-Player (120帧锁定) ===")
        print(f"颜色模式: {COLOR_MODE}")
        print("1. 播放媒体（带音频）")
        print("2. 切换颜色模式 (classic ↔ rainbow)")
        print("3. 退出")
        choice = input("请选择 (1/2/3): ").strip()

        if choice == '1':
            select_and_process_file(media_dir)
        elif choice == '2':
            COLOR_MODE = 'rainbow' if COLOR_MODE == 'classic' else 'classic'
            print(f"已切换到: {COLOR_MODE}")
            time.sleep(1)
        elif choice == '3':
            print("再见！")
            break
        else:
            input("无效，按回车重试...")

if __name__ == "__main__":
    main()