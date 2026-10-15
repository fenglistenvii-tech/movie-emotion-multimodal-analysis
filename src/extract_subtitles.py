import os
import subprocess
import sys
import json


def get_ffmpeg_exe():
    ffmpeg_exe = "ffmpeg"
    ffprobe_exe = "ffprobe"
    if sys.platform == "win32":
        if os.path.exists("ffmpeg.exe"): ffmpeg_exe = "ffmpeg.exe"
        if os.path.exists("ffprobe.exe"): ffprobe_exe = "ffprobe.exe"
    return ffmpeg_exe, ffprobe_exe


def analyze_subtitle_streams(mkv_path, ffprobe_exe):
    if not os.path.exists(mkv_path):
        raise FileNotFoundError(f"MKV 文件不存在: {mkv_path}")

    cmd = [
        ffprobe_exe, "-v", "quiet", "-print_format", "json",
        "-show_streams", "-select_streams", "s", mkv_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe 执行失败: {result.stderr}")

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        subtitle_info_list = []

        for stream in streams:
            index = stream.get("index")
            codec_name = stream.get("codec_name", "unknown")
            tags = stream.get("tags", {})
            language = tags.get("language", "und")
            title = tags.get("title", "")

            desc = f"索引:{index} | 编码:{codec_name} | 语言:{language}"
            if title: desc += f" | 标题:{title}"

            subtitle_info_list.append({
                "index": index,
                "language": language,
                "title": title,
                "codec": codec_name,
                "description": desc
            })
        return subtitle_info_list
    except Exception as e:
        raise RuntimeError(f"分析失败: {e}")


def extract_subtitle_from_mkv(mkv_path, output_path=None, selected_index=None):
    ffmpeg_exe, ffprobe_exe = get_ffmpeg_exe()

    print(f"📦 正在分析 {os.path.basename(mkv_path)} ...")
    try:
        subtitles = analyze_subtitle_streams(mkv_path, ffprobe_exe)
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

    if not subtitles:
        print("❌ 未找到任何字幕流。")
        sys.exit(1)

    print("\n--- 发现的字幕流 ---")
    for i, sub in enumerate(subtitles):
        is_chinese = 'chi' in sub['language'] or 'chinese' in sub['title'].lower()
        highlight = " 🇨🇳" if is_chinese else ""
        marker = " [默认]" if selected_index is None and i == 0 else ""
        codec_warning = " ⚠️图片格式(需OCR)" if sub['codec'] == 'hdmv_pgs_subtitle' else ""
        print(f"{i}. {sub['description']}{highlight}{marker}{codec_warning}")

    target_stream = None

    # --- 选择逻辑 ---
    if selected_index is not None:
        for sub in subtitles:
            if sub['index'] == selected_index:
                target_stream = sub
                break
        if not target_stream:
            print(f"❌ 未找到索引 {selected_index}")
            sys.exit(1)
    else:
        print("\n💡 输入序号选择 (直接回车选第一个):")
        user_input = input("> ").strip()
        if not user_input:
            target_stream = subtitles[0]
        else:
            try:
                idx = int(user_input)
                if 0 <= idx < len(subtitles):
                    target_stream = subtitles[idx]
                else:
                    print("❌ 序号越界")
                    sys.exit(1)
            except ValueError:
                print("❌ 请输入数字")
                sys.exit(1)

    # --- PGS 拦截逻辑 ---
    if target_stream['codec'] == 'hdmv_pgs_subtitle':
        print("\n" + "=" * 60)
        print("⛔ 无法直接提取文本！")
        print("=" * 60)
        print(f"选择的流是 **PGS (图片格式)**，FFmpeg 无法直接转为文本。")
        text_subs = [s for s in subtitles if s['codec'] in ['subrip', 'ass', 'ssa']]
        if text_subs:
            print(f"\n检测到可用的文本字幕:")
            for s in text_subs:
                print(f"   - {s['description']}")
            choice = input("是否改提这些文本字幕？(y/n): ").strip().lower()
            if choice == 'y':
                target_stream = text_subs[0]
                print(f"-> 已切换至: {target_stream['description']}")
            else:
                sys.exit(0)
        else:
            sys.exit(0)

    # ================= 核心修复：动态选择提取策略 =================

    source_codec = target_stream['codec']
    use_copy_mode = True  # 默认使用复制模式 (快)
    output_ext = f".{source_codec}"

    # 如果源不是 srt/subrip，询问用户是否需要转换
    if source_codec not in ['subrip', 'srt']:
        print("\n" + "=" * 60)
        print(f"📝 检测到源格式为: {source_codec.upper()}")
        print("=" * 60)
        print("请选择提取模式:")
        print("1. [推荐] 原始格式提取 (快，保留特效，后缀 .ass/.ssa)")
        print("   -> 适合多模态分析 (配合 pysubs2 库读取)")
        print("2. 强制转换为 SRT (慢，丢失特效，后缀 .srt)")
        print("   -> 适合只接受 .srt 的旧系统")

        while True:
            choice = input("\n请输入选项 (1 或 2，默认 1): ").strip()
            if choice == '' or choice == '1':
                use_copy_mode = True
                output_ext = f".{source_codec}"
                print("-> 已选择：原始格式提取 (Copy Mode)")
                break
            elif choice == '2':
                use_copy_mode = False
                output_ext = ".srt"
                print("-> 已选择：强制转换 SRT (Transcode Mode)")
                print("   ⚠️ 警告：转换长电影可能需要数分钟，请耐心等待...")
                break
            else:
                print("❌ 无效输入，请重试。")
    else:
        # 源本身就是 srt/subrip，直接复制
        use_copy_mode = True
        output_ext = ".srt"
        print("-> 源格式已是 SRT/SubRip，将直接复制提取。")

    # 生成输出文件名
    if output_path is None:
        base = os.path.splitext(mkv_path)[0]
        lang = target_stream['language'] if target_stream['language'] != 'und' else 'sub'
        # 避免双重后缀 (如 .chi.srt.srt)
        if base.endswith(lang):
            output_file = f"{base}{output_ext}"
        else:
            output_file = f"{base}.{lang}{output_ext}"
    else:
        output_file = output_path
        # 如果用户指定了路径但扩展名不匹配策略，给出警告并修正
        if not output_file.endswith(output_ext):
            print(f"⚠️ 警告：用户指定的后缀与选择模式不符，将强制修改为 {output_ext}")
            name, _ = os.path.splitext(output_file)
            output_file = name + output_ext

    # 构建命令
    stream_map = f"0:{target_stream['index']}"

    if use_copy_mode:
        codec_args = ["-c:s", "copy"]
        timeout_val = 60  # 复制模式很快，60秒足够
    else:
        codec_args = ["-c:s", "srt"]
        timeout_val = 600  # 转码模式很慢，给10分钟

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", mkv_path,
        "-map", stream_map,
        *codec_args,
        "-an", "-vn",
        output_file
    ]

    print(f"\n📥 正在处理: {target_stream['description']}")
    print(f"   策略: {'Copy (原始)' if use_copy_mode else 'Transcode (转SRT)'}")
    print(f"   输出: {output_file}")
    print(f"   超时限制: {timeout_val} 秒")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=timeout_val
        )

        if result.returncode == 0 and os.path.exists(output_file):
            if os.path.getsize(output_file) == 0:
                print("⚠️ 警告：提取的文件大小为 0。")
                print("错误详情:", result.stderr)
                sys.exit(1)

            print("✅ 处理成功！")
            print(f"   文件路径: {output_file}")

            # 提示后续步骤
            if not use_copy_mode:
                print("💡 提示：已转换为 SRT，可直接使用。")
            else:
                print(
                    "💡 提示：提取的是原始格式。若在 Python 中分析，建议使用 `pip install pysubs2` 来统一读取 .ass 和 .srt。")

            return output_file
        else:
            print("❌ 处理失败！FFmpeg 输出:")
            print(result.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        mode_str = "转码(SRT)" if not use_copy_mode else "复制"
        print(f"⚠️ {mode_str} 过程超时（超过 {timeout_val} 秒）。")
        if not use_copy_mode:
            print("💡 建议：电影太长导致转码缓慢。下次尝试选择 '1. 原始格式提取'，速度极快且不影响多模态分析。")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 配置区域
    MKV_FILE = r"E:\movie\Titanic.1997.2160p.BluRay.REMUX.HEVC.DTS-X.7.1.mkv"
    FORCE_STREAM_INDEX = None  # 设置为 None 以手动选择，或填入数字如 18

    if not os.path.exists(MKV_FILE):
        print(f"❌ 文件不存在: {MKV_FILE}")
        sys.exit(1)

    try:
        extract_subtitle_from_mkv(MKV_FILE, selected_index=FORCE_STREAM_INDEX)
    except Exception as e:
        print(f"💥 程序终止: {e}")
        sys.exit(1)