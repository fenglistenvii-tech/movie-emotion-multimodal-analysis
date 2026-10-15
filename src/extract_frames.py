import os
import cv2
import pysrt
import pandas as pd
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import threading
import queue
import traceback


def parse_srt(srt_path, log_callback=None):
    """解析字幕文件"""
    subs = None
    for enc in ['utf-8', 'gbk', 'utf-8-sig']:
        try:
            subs = pysrt.open(srt_path, encoding=enc)
            if log_callback:
                log_callback(f"✅ 字幕解析成功 (编码: {enc})")
            break
        except Exception:
            continue

    if not subs:
        raise ValueError("❌ 无法解析字幕文件，请检查文件或编码")

    data = []
    for sub in subs:
        start = sub.start.ordinal / 1000.0
        end = sub.end.ordinal / 1000.0
        text = sub.text.replace('\n', ' ').strip()
        if text:
            data.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'text': text
            })
    return pd.DataFrame(data)


def has_face(frame, detector):
    """
    检测当前帧是否有人脸
    包含自动缩放优化：将大图缩小到 320px 宽再检测，大幅提升速度且不影响精度
    """
    h, w = frame.shape[:2]

    # 优化：如果图片太大，先缩小再检测 (BlazeFace 不需要 4K 分辨率)
    target_w = 320
    if w > target_w:
        scale = target_w / w
        new_h = int(h * scale)
        small_frame = cv2.resize(frame, (target_w, new_h), interpolation=cv2.INTER_LINEAR)
    else:
        small_frame = frame

    # BGR -> RGB
    rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect(mp_img)

    if result.detections:
        return True, len(result.detections)
    return False, 0


def run_extract_subtitles(video_path, srt_path, output_dir, fps_target, log_callback=None):
    """封装 extract_subtitles 的主逻辑"""
    if log_callback is None:
        log_callback = print
    try:
        MODEL_NAME = "blaze_face_short_range.tflite"
        if not os.path.exists(MODEL_NAME):
            raise FileNotFoundError(f"❌ 找不到模型文件 '{MODEL_NAME}'!")

        model_path = os.path.abspath(MODEL_NAME)
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(base_options=base_options, running_mode=vision.RunningMode.IMAGE)
        detector = vision.FaceDetector.create_from_options(options)

        # 主流程
        log_callback("📄 解析字幕...")
        df_sub = parse_srt(srt_path, log_callback)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError("无法打开视频")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, int(fps / fps_target))

        os.makedirs(output_dir, exist_ok=True)
        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        # === 队列与共享状态 ===
        q_read = queue.Queue(maxsize=5)  # Reader -> Detector
        q_write = queue.Queue(maxsize=5)  # Detector -> Writer

        records = []
        saved_count = 0
        skipped_count = 0
        stop_flag = False

        # === 线程函数定义 ===

        def reader_thread():
            """生产者：读取视频帧"""
            current_frame_id = 0
            while not stop_flag:
                # 【核心优化】直接跳转到目标帧，避免解码中间无用的帧
                target_pos = current_frame_id + interval

                if current_frame_id > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_pos)

                ret, frame = cap.read()
                if not ret:
                    break

                # 获取实际帧号 (防止 set 不精准)
                actual_frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                timestamp = actual_frame_id / fps

                # 放入队列
                q_read.put({
                    'frame_id': actual_frame_id,
                    'timestamp': timestamp,
                    'frame': frame
                })

                current_frame_id = actual_frame_id

            # 发送结束信号
            q_read.put(None)

        def detector_thread():
            """消费者 1：人脸检测"""
            while True:
                item = q_read.get()
                if item is None:
                    q_write.put(None)
                    break

                # 执行检测
                has_face_flag, face_count = has_face(item['frame'], detector)

                item['has_face'] = has_face_flag
                item['face_count'] = face_count

                q_write.put(item)
                q_read.task_done()

        def writer_thread():
            """消费者 2：保存结果"""
            nonlocal saved_count, skipped_count

            while True:
                item = q_write.get()
                if item is None:
                    break

                if item['has_face']:
                    timestamp = item['timestamp']

                    # 匹配字幕
                    match = df_sub[(df_sub['start'] <= timestamp) & (df_sub['end'] >= timestamp)]
                    text = ""
                    if not match.empty:
                        text = match.iloc[0]['text']

                    # 保存图片
                    img_name = f"frame_{saved_count:05d}.jpg"
                    img_path = os.path.join(frames_dir, img_name)
                    cv2.imwrite(img_path, item['frame'])

                    # 记录数据
                    records.append({
                        'id': saved_count,
                        'time': round(timestamp, 2),
                        'src_frame': item['frame_id'],
                        'img': os.path.relpath(img_path, output_dir),
                        'text': text,
                        'faces': item['face_count']
                    })
                    saved_count += 1
                else:
                    skipped_count += 1

                # 每处理50帧更新一次运行状态
                processed = saved_count + skipped_count
                if processed % 50 == 0:
                    log_callback(f"⏳ 正在抽帧处理中...")

                q_write.task_done()

        # === 启动线程 ===
        t_reader = threading.Thread(target=reader_thread)
        t_detector = threading.Thread(target=detector_thread)
        t_writer = threading.Thread(target=writer_thread)

        t_reader.start()
        t_detector.start()
        t_writer.start()

        # 等待所有线程结束
        t_reader.join()
        t_detector.join()
        t_writer.join()

        cap.release()
        
        # 任务完成
        log_callback(f"✅ 抽帧处理完成")

        if records:
            df_out = pd.DataFrame(records)
            csv_path = os.path.join(output_dir, "dataset.csv")
            df_out.to_csv(csv_path, index=False, encoding='utf-8')
            log_callback(f"\n✅ 完成! 保留 {saved_count} 帧，数据保存至: {csv_path}")
        else:
            log_callback("⚠️ 未检测到含人脸的帧。")
    except Exception as e:
        log_callback(f"💥 错误: {str(e)}\n{traceback.format_exc()}")


# ==============================
# 🚀 主执行流程 (保留以便单独运行)
# ==============================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        video_path = sys.argv[1]
        srt_path = sys.argv[2]
        output_dir = sys.argv[3]
        fps_target = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    else:
        video_path = r"E:\movie\Your.Name.2016.2160p.BluRay.x265.10bit.HDR.DTS-HD.MA.5.1-SWTYBLZ.mkv"
        srt_path = r"E:\movie\Your.Name.2016.2160p.BluRay.x265.10bit.HDR.DTS-HD.MA.5.1-SWTYBLZ.srt"
        output_dir = "1.Dataset"
        fps_target = 0.2
    
    def print_callback(msg):
        print(msg)
    
    run_extract_subtitles(video_path, srt_path, output_dir, fps_target, print_callback)