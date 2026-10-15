import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from snownlp import SnowNLP
from deepface import DeepFace
import warnings
import traceback

# 忽略不必要的警告，保持输出整洁
warnings.filterwarnings("ignore")


def analyze_text_sentiment(text):
    """使用 SnowNLP 分析文本情感，返回 0-1 之间的分数"""
    if not isinstance(text, str):
        return 0.5  # 空文本默认为中性
    
    # 清理文本噪声
    import re
    # 1. 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 2. 移除ASS/SSA样式代码（如{\c&HFFFFFF&}等）
    clean_text = re.sub(r'{[^}]+}', '', clean_text)
    # 3. 移除多余的空白字符
    clean_text = re.sub(r'\s+', ' ', clean_text)
    # 4. 去除首尾空白
    clean_text = clean_text.strip()
    
    if not clean_text:
        return 0.5  # 空文本默认为中性
    
    try:
        s = SnowNLP(clean_text)
        return s.sentiments
    except Exception:
        return 0.5


def analyze_visual_emotion(image_path):
    """
    使用 DeepFace 分析图片情感。
    返回主导情绪的概率字典 (happy, sad, etc.) 和主导情绪名称。
    """
    if not os.path.exists(image_path):
        return None, None

    try:
        # 关键配置：enforce_detection=False 防止无人脸时崩溃
        result = DeepFace.analyze(
            img_path=image_path,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend='opencv',
            align=True,
            silent=True
        )

        # 处理返回结果结构
        if isinstance(result, list):
            if len(result) > 0:
                result = result[0]
            else:
                return None, None

        emotions = result['emotion']
        dominant_emotion = result['dominant_emotion']

        # 提取 Happy 和 Sad 的概率 (0-100)
        happy_prob = emotions.get('happy', 0)
        sad_prob = emotions.get('sad', 0)

        return {'happy': happy_prob, 'sad': sad_prob}, dominant_emotion

    except Exception as e:
        return None, None


def plot_emotions(df, output_dir, start_idx=None, end_idx=None):
    """生成原始数据图和平滑趋势图"""
    # 设置中文字体
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass

    plt.style.use('seaborn-v0_8-whitegrid')

    # 数据已经在run_analyze_emotions中筛选过，这里不需要再次筛选

    x = df['time']

    # ==============================
    # 📊 数据预处理：计算平滑数据
    # ==============================
    df['text_scaled'] = df['text_sentiment_score'] * 100
    window_size = 7

    df['happy_smooth'] = df['happy'].rolling(window=window_size, center=True, min_periods=1).mean()
    df['sad_smooth'] = df['sad'].rolling(window=window_size, center=True, min_periods=1).mean()
    df['text_smooth'] = df['text_scaled'].rolling(window=window_size, center=True, min_periods=1).mean()

    # ==============================
    # 🖼️ 图 1: 原始数据图 (Raw Data)
    # ==============================
    fig_raw, ax_raw = plt.subplots(figsize=(14, 7))

    ax_raw.plot(x, df['text_scaled'], label='Text Sentiment (Scaled)', color='#1f77b4', linewidth=1.5, alpha=0.8)
    ax_raw.plot(x, df['happy'], label='Visual: Happy (Raw)', color='#d62728', linestyle='--', linewidth=1, alpha=0.6)
    ax_raw.plot(x, df['sad'], label='Visual: Sad (Raw)', color='#2ca02c', linestyle=':', linewidth=1, alpha=0.6)

    ax_raw.axhline(y=50, color='gray', linestyle='-', linewidth=1, alpha=0.3, label='Neutral Line')
    ax_raw.set_title(f'Raw Multimodal Emotion Analysis', fontsize=14, fontweight='bold')
    ax_raw.set_xlabel('Time (seconds)', fontsize=12)
    ax_raw.set_ylabel('Score / Probability (%)', fontsize=12)
    ax_raw.legend(loc='upper right', fontsize=10)

    ax_raw.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{int(x // 60)}:{int(x % 60):02d}'))
    ax_raw.set_ylim(0, 105)
    plt.tight_layout()

    path_raw = os.path.join(output_dir, "emotion_timeline_raw.png")
    plt.savefig(path_raw, dpi=300)
    plt.close(fig_raw)

    # ==============================
    # 📈 图 2: 平滑趋势图 (Smoothed Trend)
    # ==============================
    fig_smooth, ax_smooth = plt.subplots(figsize=(14, 7))

    ax_smooth.plot(x, df['text_smooth'], label='Text Sentiment (Trend)', color='#1f77b4', linewidth=2.5, alpha=0.9)
    ax_smooth.plot(x, df['happy_smooth'], label='Visual: Happy (Trend)', color='#d62728', linestyle='-', linewidth=2.5,
                   alpha=0.8)
    ax_smooth.plot(x, df['sad_smooth'], label='Visual: Sad (Trend)', color='#2ca02c', linestyle='-', linewidth=2.5,
                   alpha=0.8)

    ax_smooth.axhline(y=50, color='gray', linestyle='-', linewidth=1, alpha=0.3, label='Neutral Line')
    ax_smooth.set_title(f'Smoothed Multimodal Emotion Trends (Window={window_size})', fontsize=14, fontweight='bold')
    ax_smooth.set_xlabel('Time (seconds)', fontsize=12)
    ax_smooth.set_ylabel('Smoothed Score / Probability (%)', fontsize=12)
    ax_smooth.legend(loc='upper right', fontsize=10)

    ax_smooth.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{int(x // 60)}:{int(x % 60):02d}'))
    ax_smooth.set_ylim(0, 105)
    plt.tight_layout()

    path_smooth = os.path.join(output_dir, "emotion_timeline_smoothed.png")
    plt.savefig(path_smooth, dpi=300)
    plt.close(fig_smooth)


def run_analyze_emotions(dataset_root, start_idx=None, end_idx=None, log_callback=None):
    """封装 analyze_emotions 的主逻辑，支持范围选择"""
    if log_callback is None:
        log_callback = print
    try:
        DATASET_FILE = os.path.join(dataset_root, "dataset.csv")
        FRAMES_DIR = os.path.join(dataset_root, "frames")
        OUTPUT_DIR = dataset_root

        if not os.path.exists(DATASET_FILE):
            raise FileNotFoundError("找不到 dataset.csv")
        if not os.path.exists(FRAMES_DIR):
            raise FileNotFoundError("找不到 frames 文件夹")

        # 尝试多种编码读取CSV文件
        encodings = ['utf-8', 'gbk', 'utf-8-sig', 'cp936']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(DATASET_FILE, encoding=enc)
                print(f"✅ CSV文件读取成功 (编码: {enc})")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("❌ 无法读取CSV文件，请检查文件编码")
        required_cols = ['time', 'text']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("CSV 缺少必要列")

        # 应用范围筛选
        original_len = len(df)
        if start_idx is not None and end_idx is not None:
            df = df.iloc[start_idx:end_idx+1].copy()
        elif start_idx is not None:
            df = df.iloc[start_idx:].copy()
        elif end_idx is not None:
            df = df.iloc[:end_idx+1].copy()

        df['text_sentiment_score'] = 0.0
        df['happy'] = 0.0
        df['sad'] = 0.0
        df['dominant_visual_emotion'] = ""

        total = len(df)
        found_count = 0
        for idx, row in df.iterrows():
            # 文本分析
            score = analyze_text_sentiment(row['text'])
            df.at[idx, 'text_sentiment_score'] = score

            # 视觉分析
            img_path1 = os.path.join(FRAMES_DIR, f"frame_{idx:05d}.jpg")
            img_path2 = os.path.join(FRAMES_DIR, f"frame_{idx+1:05d}.jpg")
            img_path = img_path1 if os.path.exists(img_path1) else (img_path2 if os.path.exists(img_path2) else None)

            if img_path:
                found_count += 1
                emotions, dom = analyze_visual_emotion(img_path)
                if emotions:
                    df.at[idx, 'happy'] = emotions['happy']
                    df.at[idx, 'sad'] = emotions['sad']
                    df.at[idx, 'dominant_visual_emotion'] = dom
                else:
                    df.at[idx, 'dominant_visual_emotion'] = "No Face"
            else:
                df.at[idx, 'dominant_visual_emotion'] = "Image Missing"

            if (idx - (start_idx if start_idx is not None else 0) + 1) % 50 == 0:
                log_callback(f"分析进度: {idx - (start_idx if start_idx is not None else 0) + 1}/{total}")

        # 保存结果
        output_csv = os.path.join(OUTPUT_DIR, "dataset_some_analysis.csv")
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')

        # 绘图
        plot_emotions(df, OUTPUT_DIR, start_idx, end_idx)

        log_callback(f"\n✅ 情感分析完成! 结果保存至:\n{output_csv}\n{OUTPUT_DIR}")
        log_callback(f"分析范围: {start_idx if start_idx is not None else 0} 到 {end_idx if end_idx is not None else original_len-1}")
        if found_count < total * 0.5:
            log_callback("⚠️ 提示: 匹配图片较少，请检查 frames/ 中的文件名。")

    except Exception as e:
        log_callback(f"💥 分析出错: {str(e)}\n{traceback.format_exc()}")


# ==============================
# 🚀 主执行流程 (保留以便单独运行)
# ==============================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        dataset_root = sys.argv[1]
        start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else None
        end_idx = int(sys.argv[3]) if len(sys.argv) > 3 else None
    else:
        dataset_root = r"F:\Personal\Titanic.Dataset"
        start_idx = 531
        end_idx = 563
    
    def print_callback(msg):
        print(msg)
    
    run_analyze_emotions(dataset_root, start_idx, end_idx, print_callback)