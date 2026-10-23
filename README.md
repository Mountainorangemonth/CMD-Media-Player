# CMD 媒体播放器

这是一个能在终端窗口中，将图片和视频文件以彩色 ASCII 字符画形式播放的 Python 程序。

> **v1.2 已更新**：视频**现在有声音了**；主程序重写为三线程流水线并锁定 120 帧；`media/` 不再入库。详见下方「本次更新对比」。

## ✨ 主要功能

- **图片播放**：`.jpg` / `.png` / `.jpeg` / `.bmp` / `.gif` → 彩色 ASCII 字符画。
- **视频播放（带音频）**：逐帧读取视频并在终端内播放动画，同时用 `ffmpeg` 提取音轨、`ffplay` 在屏幕外播放，画面与声音同步。
- **彩色渲染**：24 位真彩 ANSI，两种模式可切 —— `classic`（保留原色）与 `rainbow`（彩虹渐变）。
- **智能缩放**：按终端窗口尺寸等比缩放并居中，不滚动、不抽搐。
- **120 帧锁定**：按视频原始帧率播放（上限 120 FPS），落后时丢帧而不是累积延迟。
- **自动全屏**：启动时自动按 F11（依赖 `pyautogui`），失败则提示手动按。
- **跨平台**：基于 Python 与标准库构建，Windows / macOS / Linux 均可运行（音频依赖 ffmpeg 与 ffplay）。

## 📦 下载即用（Windows，无需安装 Python）

打包好的单文件程序（约 145 MB，内部已包含 `ffmpeg.exe` 与 `ffplay.exe`）：

- **v1.2**：[`CMD-Media-Player.exe`](https://github.com/Mountainorangemonth/CMD-Media-Player/releases/download/v1.2/CMD-Media-Player.exe)
- 全部版本：<https://github.com/Mountainorangemonth/CMD-Media-Player/releases>

下载后放到任意目录双击运行，首次启动会在程序同目录自动创建 `media/` 文件夹。

## 🔄 本次更新对比（v1.1 → v1.2）

| 项目 | 之前（v1.1 及更早） | 现在（v1.2） |
|---|---|---|
| **音频** | 纯画面，完全无声 | **视频带声音**：`ffmpeg` 抽音轨到临时 wav，`ffplay` 在屏幕外播放，退出时自动删除临时文件 |
| `main.py` | 5,455 字节，单线程逐帧转换 | 12,106 字节（PR #1：+282 / −85 行） |
| **渲染管线** | 单线程：读帧 → 转 ASCII → 输出，三者互相阻塞 | 三线程 + 双队列（读帧 / 转 ASCII / 渲染），互不阻塞 |
| **帧率控制** | 跟随处理速度，忽快忽慢 | 按原始帧率播放，上限 120 FPS，落后丢帧不累积延迟 |
| **字符集** | 95 级灰度字符表 | `ASCII_CHARS = " *"`，主要靠颜色表现画面（想更细腻可改这一行） |
| **颜色模式** | 固定，只能在代码里改 | 菜单可随时切换 `classic` ↔ `rainbow` |
| **全屏** | 手动按 F11 | 启动自动按 F11（`pyautogui`），失败提示手动 |
| **依赖** | Pillow、opencv-python、numpy | Pillow、opencv-python、pyautogui、moviepy\* |
| **`运行.cmd`** | 写死 `E:\py\python.exe E:\1\ascii_player\main.py` | 改为 `python main.py`，换台机器直接能用 |
| **`media/`** | 仓库里带着 `演示图片.jpg` | 不再入库，首次运行自动创建 |
| **打包** | 无 | 新增 `CMD-Media-Player.spec`，发布 Release v1.2（内置 ffmpeg/ffplay） |
| **`.gitignore`** | 无 | 忽略 `build/`、`dist/`、`media/`、`__pycache__/` |

\* `moviepy` 目前并未被 `main.py` 调用，实际运行只用到 Pillow、opencv-python、pyautogui，可以按需删除。

## 📁 项目结构

```
CMD-Media-Player/
├── main.py                  # 主程序（终端 ASCII 播放器，带音频）
├── main_v2_rainbow.py       # 彩虹渲染变体（独立脚本，不参与打包）
├── media/                   # 运行时自动创建，放你的图片/视频（不入库）
├── requirements.txt         # 依赖列表
├── 运行.cmd                 # (Windows) 一键运行
├── main.spec                # PyInstaller 打包脚本（无图标）
├── CMD-Media-Player.spec    # PyInstaller 打包脚本（带图标，内置 ffmpeg/ffplay）
├── favicon_ico5.net.ico     # exe 图标，仅打包时使用
├── LICENSE
└── README.md
```

## ⚙️ 环境要求

- **Python 3.x**
- **pip**（通常随 Python 一起安装）
- **ffmpeg / ffplay**：源码运行时需要，放到项目目录或加入 `PATH` 即可
  （直接下载 Release 里的 exe 则不需要，已内置）

## 🚀 安装与设置

**第一步：安装依赖库**

```bash
cd CMD-Media-Player
pip install -r requirements.txt
```

看到 `Successfully installed ...` 即表示安装成功。

**第二步：准备媒体文件**

把要播放的图片或视频放进 `media` 文件夹（没有的话程序会自动创建）。

## ▶️ 如何运行

**方法一：使用快捷命令（Windows 推荐）**

双击项目文件夹中的 `运行.cmd`。

**方法二：使用命令行**

```bash
python main.py
```

## 📋 使用说明

启动后是主菜单：

```
=== CMD-Media-Player (120帧锁定) ===
颜色模式: classic
1. 播放媒体（带音频）
2. 切换颜色模式 (classic ↔ rainbow)
3. 退出
```

1. 选 `1`，程序会列出 `media/` 里所有支持的媒体文件，输入**数字序号**回车；
2. 播放视频时自动全屏、自动出声音，按 `Ctrl + C` 停止；
3. 选 `2` 可在经典配色和彩虹渐变之间切换，下一部片生效；
4. 选 `3` 退出。

## 🔧 自己打包成 exe

```bash
pip install pyinstaller
pyinstaller CMD-Media-Player.spec
```

产物在 `dist/CMD-Media-Player.exe`。

> ⚠️ `CMD-Media-Player.spec` 里的 `icon=` 目前是**绝对路径**：
> `icon=['F:/项目/CMD-Media-Player-main/favicon_ico5.net.ico']`。
> 换台机器打包会报 `icon file not found`，把它改成相对路径 `icon=['favicon_ico5.net.ico']`，或直接删掉这一行即可。

## ⚠️ 注意事项

- **性能**：终端字体越小，要渲染的字符越多，越吃性能。播放卡顿就把字体调大一些；也可以在 `main.py` 顶部把 `MAX_FPS` 调低。
- **音频**：音频靠 `ffmpeg` 先抽取音轨再交给 `ffplay` 播放，**大文件首次播放会有几秒到几十秒的延迟**，属于正常现象。若提示「未找到 ffmpeg」，说明它不在程序目录也不在 `PATH` 里。
- **音画同步**：画面是逐帧转字符画后再输出，慢速终端上画面可能比声音略滞后。
- **画面风格**：`ASCII_CHARS = " *"` 只有两个字符，画面本质是「二色 + 真彩」，想更细腻可以把它换成更长的字符表（如渐变字符集），但渲染开销会变大。
