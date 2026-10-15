# main_ui.py
import sys
import os
import threading
import traceback

# 导入模块化函数
# 注意：run_extract_subtitles 虽然名字里有 "subtitles"，但它实现的是
#       「抽帧 + 字幕时间对齐」，所以定义在 extract_frames 模块里。
from extract_frames import run_extract_subtitles
from analyze_emotions import run_analyze_emotions

def log_callback(msg):
    """命令行日志回调函数"""
    print(msg)

def main():
    """命令行主函数"""
    if len(sys.argv) < 2:
        print("请选择操作:")
        print("1. 抽帧与字幕对齐")
        print("2. 情感分析")
        choice = input("请输入选项 (1/2): ")
    else:
        choice = sys.argv[1]
    
    if choice == "1":
        # 抽帧与字幕对齐
        if len(sys.argv) >= 5:
            video_path = sys.argv[2]
            srt_path = sys.argv[3]
            output_dir = sys.argv[4]
            fps_target = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
        else:
            video_path = input("请输入视频文件路径: ")
            srt_path = input("请输入字幕文件路径: ")
            output_dir = input("请输入输出目录: ")
            fps_target = float(input("请输入抽帧频率 (帧/秒，默认 0.2): ") or "0.2")
        
        print("\n🚀 开始抽帧与字幕对齐...")
        run_extract_subtitles(video_path, srt_path, output_dir, fps_target, log_callback)
        
    elif choice == "2":
        # 情感分析
        if len(sys.argv) >= 3:
            dataset_dir = sys.argv[2]
            start_idx = int(sys.argv[3]) if len(sys.argv) > 3 else None
            end_idx = int(sys.argv[4]) if len(sys.argv) > 4 else None
        else:
            dataset_dir = input("请输入数据集目录 (含 dataset.csv 和 frames/): ")
            start_input = input("请输入起始帧索引 (留空表示从开始): ")
            end_input = input("请输入结束帧索引 (留空表示到结束): ")
            start_idx = int(start_input) if start_input.strip() else None
            end_idx = int(end_input) if end_input.strip() else None
        
        print("\n🧠 开始情感分析...")
        run_analyze_emotions(dataset_dir, start_idx, end_idx, log_callback)
    else:
        print("无效选项，请选择 1 或 2")


# ==============================
# 🚀 启动应用
# ==============================

if __name__ == "__main__":
    try:
        # 尝试导入PyQt5，如果存在则运行GUI版本
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
            QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QProgressBar
        )
        from PyQt5.QtCore import Qt, pyqtSignal, QObject
        from PyQt5.QtGui import QPixmap
        
        class Worker(QObject):
            finished = pyqtSignal()
            log_signal = pyqtSignal(str)

            def __init__(self, func, *args):
                super().__init__()
                self.func = func
                self.args = args

            def run(self):
                try:
                    self.func(*self.args, self.log_signal.emit)
                finally:
                    self.finished.emit()

        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("🎬 多模态情感分析工具 (支持范围选择)")
                self.resize(1000, 800)

                # 存储最近的输出目录
                self.last_output_dir = ""

                # Central Widget
                central = QWidget()
                self.setCentralWidget(central)
                layout = QVBoxLayout(central)

                # Tab Widget
                self.tabs = QTabWidget()
                self.tabs.currentChanged.connect(self.tab_changed)
                layout.addWidget(self.tabs)

                # === Tab 1: 抽帧 ===
                tab1 = QWidget()
                self.tabs.addTab(tab1, "1. 抽帧与字幕对齐")
                v1 = QVBoxLayout(tab1)

                # Video
                h1 = QHBoxLayout()
                self.video_line = QLineEdit()
                btn_video = QPushButton("选择视频...")
                btn_video.clicked.connect(lambda: self.select_file(self.video_line, "视频文件 (*.mp4 *.mkv *.avi)"))
                h1.addWidget(QLabel("视频文件:"))
                h1.addWidget(self.video_line)
                h1.addWidget(btn_video)
                v1.addLayout(h1)

                # SRT
                h2 = QHBoxLayout()
                self.srt_line = QLineEdit()
                btn_srt = QPushButton("选择字幕...")
                btn_srt.clicked.connect(lambda: self.select_file(self.srt_line, "字幕文件 (*.srt)"))
                h2.addWidget(QLabel("字幕文件:"))
                h2.addWidget(self.srt_line)
                h2.addWidget(btn_srt)
                v1.addLayout(h2)

                # Output Dir
                h3 = QHBoxLayout()
                self.out_dir_line = QLineEdit()
                btn_out = QPushButton("选择输出目录...")
                btn_out.clicked.connect(lambda: self.select_folder(self.out_dir_line))
                h3.addWidget(QLabel("输出目录:"))
                h3.addWidget(self.out_dir_line)
                h3.addWidget(btn_out)
                v1.addLayout(h3)

                # FPS Target
                h4 = QHBoxLayout()
                h4.addWidget(QLabel("抽帧频率 (帧/秒):"))
                self.fps_spin = QDoubleSpinBox()
                self.fps_spin.setRange(0.01, 10)
                self.fps_spin.setValue(0.2)
                self.fps_spin.setSingleStep(0.1)
                h4.addWidget(self.fps_spin)
                h4.addStretch()
                v1.addLayout(h4)

                # First Frame Preview
                self.first_frame_label = QLabel("第一帧预览")
                self.first_frame_label.setAlignment(Qt.AlignCenter)
                self.first_frame_label.setMinimumHeight(200)
                self.first_frame_label.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
                v1.addWidget(self.first_frame_label)

                # Run Button
                self.btn_run1 = QPushButton("🚀 开始抽帧")
                self.btn_run1.clicked.connect(self.start_extraction)
                v1.addWidget(self.btn_run1)

                # === Tab 2: 情感分析 ===
                tab2 = QWidget()
                self.tabs.addTab(tab2, "2. 情感分析")
                v2 = QVBoxLayout(tab2)

                h5 = QHBoxLayout()
                self.dataset_line = QLineEdit()
                btn_dataset = QPushButton("选择数据集目录...")
                btn_dataset.clicked.connect(lambda: self.select_folder(self.dataset_line))
                h5.addWidget(QLabel("数据集目录 (含 dataset.csv 和 frames/):"))
                h5.addWidget(self.dataset_line)
                h5.addWidget(btn_dataset)
                v2.addLayout(h5)

                # 范围选择
                h6 = QHBoxLayout()
                h6.addWidget(QLabel("分析范围:"))
                self.start_spin = QSpinBox()
                self.start_spin.setMinimum(0)
                self.start_spin.setMaximum(99999)
                self.start_spin.setValue(0)
                h6.addWidget(QLabel("起始帧:"))
                h6.addWidget(self.start_spin)
                h6.addWidget(QLabel("结束帧:"))
                self.end_spin = QSpinBox()
                self.end_spin.setMinimum(0)
                self.end_spin.setMaximum(99999)
                self.end_spin.setValue(99999)
                h6.addWidget(self.end_spin)
                h6.addStretch()
                v2.addLayout(h6)

                # 范围提示
                self.range_tip = QLabel("提示: 留空或设置为99999表示到结束")
                self.range_tip.setStyleSheet("color: #666; font-style: italic;")
                v2.addWidget(self.range_tip)

                # 最近使用提示
                self.last_used_label = QLabel("最近使用: 无")
                self.last_used_label.setStyleSheet("color: #666; font-style: italic;")
                v2.addWidget(self.last_used_label)

                self.btn_run2 = QPushButton("🧠 开始情感分析")
                self.btn_run2.clicked.connect(self.start_analysis)
                v2.addWidget(self.btn_run2)

                # Emotion Plots
                self.plot_layout = QHBoxLayout()
                self.raw_plot_label = QLabel("原始数据图")
                self.raw_plot_label.setAlignment(Qt.AlignCenter)
                self.raw_plot_label.setMinimumHeight(300)
                self.raw_plot_label.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
                
                self.smoothed_plot_label = QLabel("平滑趋势图")
                self.smoothed_plot_label.setAlignment(Qt.AlignCenter)
                self.smoothed_plot_label.setMinimumHeight(300)
                self.smoothed_plot_label.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
                
                self.plot_layout.addWidget(self.raw_plot_label)
                self.plot_layout.addWidget(self.smoothed_plot_label)
                v2.addLayout(self.plot_layout)

                # Log Area
                self.log_area = QTextEdit()
                self.log_area.setReadOnly(True)
                layout.addWidget(self.log_area)



                self.thread = None
                self.worker = None

            def select_file(self, line_edit, filter_str):
                path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter_str)
                if path:
                    line_edit.setText(path)

            def select_folder(self, line_edit):
                path = QFileDialog.getExistingDirectory(self, "选择目录")
                if path:
                    line_edit.setText(path)

            def log_message(self, msg):
                # 在UI线程中更新日志
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(self.log_area, "append", Qt.QueuedConnection, Q_ARG(str, msg))

            def start_extraction(self):
                video = self.video_line.text().strip()
                srt = self.srt_line.text().strip()
                out_dir = self.out_dir_line.text().strip()
                fps = self.fps_spin.value()

                if not all([video, srt, out_dir]):
                    QMessageBox.warning(self, "输入错误", "请填写所有路径！")
                    return
                if not os.path.isfile(video):
                    QMessageBox.warning(self, "错误", "视频文件不存在！")
                    return
                if not os.path.isfile(srt):
                    QMessageBox.warning(self, "错误", "字幕文件不存在！")
                    return

                # 保存输出目录作为最近使用的目录
                self.last_output_dir = out_dir
                # 更新最近使用提示
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(self.last_used_label, "setText", Qt.QueuedConnection, 
                                        Q_ARG(str, f"最近使用: {os.path.basename(out_dir)}"))

                self.run_worker(run_extract_subtitles, video, srt, out_dir, fps)

            def tab_changed(self, index):
                """标签页切换时的处理"""
                # 当切换到情感分析标签页时
                if index == 1 and self.last_output_dir:
                    # 自动填充最近使用的输出目录
                    self.dataset_line.setText(self.last_output_dir)
                    # 更新最近使用提示
                    self.last_used_label.setText(f"最近使用: {os.path.basename(self.last_output_dir)}")

            def start_analysis(self):
                dataset_dir = self.dataset_line.text().strip()
                if not dataset_dir or not os.path.isdir(dataset_dir):
                    QMessageBox.warning(self, "错误", "请选择有效的数据集目录！")
                    return
                
                # 获取范围值
                start_idx = self.start_spin.value()
                end_idx = self.end_spin.value()
                
                # 如果end_idx设置为99999，则视为None（到结束）
                if end_idx == 99999:
                    end_idx = None
                
                self.run_worker(run_analyze_emotions, dataset_dir, start_idx, end_idx)

            def run_worker(self, func, *args):
                self.btn_run1.setEnabled(False)
                self.btn_run2.setEnabled(False)
                self.log_area.clear()
                
                # 创建Worker对象
                self.worker = Worker(func, *args)
                self.worker.log_signal.connect(self.log_message)
                self.worker.finished.connect(self.worker_finished)
                
                # 启动线程
                from PyQt5.QtCore import QThread
                self.thread = QThread()
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.run)
                self.thread.start()

            def display_first_frame(self, output_dir):
                """显示抽帧的第一帧"""
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                import glob
                
                # 尝试多种可能的路径格式
                possible_patterns = [
                    os.path.join(output_dir, "frames", "frame_*.jpg"),
                    os.path.join(output_dir, "frame_*.jpg")
                ]
                
                first_frame_path = None
                # 尝试所有模式
                for pattern in possible_patterns:
                    files = glob.glob(pattern)
                    if files:
                        # 按文件名排序，取第一个
                        files.sort()
                        first_frame_path = files[0]
                        break
                
                if first_frame_path:
                    # 输出路径信息到日志
                    QMetaObject.invokeMethod(self.log_area, "append", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, f"📷 找到第一帧: {first_frame_path}"))
                    
                    pixmap = QPixmap(first_frame_path)
                    if not pixmap.isNull():
                        # 缩放图像以适应标签
                        scaled_pixmap = pixmap.scaled(self.first_frame_label.size(), 
                                                  Qt.KeepAspectRatio, 
                                                  Qt.SmoothTransformation)
                        QMetaObject.invokeMethod(self.first_frame_label, "setPixmap", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(QPixmap, scaled_pixmap))
                        QMetaObject.invokeMethod(self.first_frame_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, ""))
                    else:
                        QMetaObject.invokeMethod(self.first_frame_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, "无法加载图像"))
                        QMetaObject.invokeMethod(self.log_area, "append", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, "⚠️ 无法加载第一帧图像"))
                else:
                    QMetaObject.invokeMethod(self.first_frame_label, "setText", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, "未找到第一帧"))
                    QMetaObject.invokeMethod(self.log_area, "append", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, "⚠️ 未找到第一帧图像"))
                    # 输出所有尝试的模式
                    for pattern in possible_patterns:
                        QMetaObject.invokeMethod(self.log_area, "append", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, f"  尝试模式: {pattern}"))

            def display_emotion_plots(self, dataset_dir):
                """显示情感分析的两张图像"""
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                
                raw_plot_path = os.path.join(dataset_dir, "emotion_timeline_raw.png")
                smoothed_plot_path = os.path.join(dataset_dir, "emotion_timeline_smoothed.png")
                
                # 显示原始数据图
                if os.path.exists(raw_plot_path):
                    pixmap = QPixmap(raw_plot_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.raw_plot_label.size(), 
                                                  Qt.KeepAspectRatio, 
                                                  Qt.SmoothTransformation)
                        QMetaObject.invokeMethod(self.raw_plot_label, "setPixmap", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(QPixmap, scaled_pixmap))
                        QMetaObject.invokeMethod(self.raw_plot_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, ""))
                    else:
                        QMetaObject.invokeMethod(self.raw_plot_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, "无法加载图像"))
                else:
                    QMetaObject.invokeMethod(self.raw_plot_label, "setText", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, "未找到原始数据图"))
                
                # 显示平滑趋势图
                if os.path.exists(smoothed_plot_path):
                    pixmap = QPixmap(smoothed_plot_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.smoothed_plot_label.size(), 
                                                  Qt.KeepAspectRatio, 
                                                  Qt.SmoothTransformation)
                        QMetaObject.invokeMethod(self.smoothed_plot_label, "setPixmap", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(QPixmap, scaled_pixmap))
                        QMetaObject.invokeMethod(self.smoothed_plot_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, ""))
                    else:
                        QMetaObject.invokeMethod(self.smoothed_plot_label, "setText", 
                                               Qt.QueuedConnection, 
                                               Q_ARG(str, "无法加载图像"))
                else:
                    QMetaObject.invokeMethod(self.smoothed_plot_label, "setText", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, "未找到平滑趋势图"))

            def worker_finished(self):
                # 线程完成时的处理
                self.btn_run1.setEnabled(True)
                self.btn_run2.setEnabled(True)
                
                # 显示相应的图像
                current_tab = self.tabs.currentIndex()
                if current_tab == 0 and self.last_output_dir:
                    # 抽帧完成，显示第一帧
                    self.display_first_frame(self.last_output_dir)
                elif current_tab == 1 and self.dataset_line.text().strip():
                    # 情感分析完成，显示图像
                    dataset_dir = self.dataset_line.text().strip()
                    self.display_emotion_plots(dataset_dir)
                    # 输出路径信息到日志
                    from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                    raw_plot_path = os.path.join(dataset_dir, "emotion_timeline_raw.png")
                    smoothed_plot_path = os.path.join(dataset_dir, "emotion_timeline_smoothed.png")
                    QMetaObject.invokeMethod(self.log_area, "append", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, f"📊 尝试加载图像:"))
                    QMetaObject.invokeMethod(self.log_area, "append", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, f"  原始数据图: {raw_plot_path} (存在: {os.path.exists(raw_plot_path)})"))
                    QMetaObject.invokeMethod(self.log_area, "append", 
                                           Qt.QueuedConnection, 
                                           Q_ARG(str, f"  平滑趋势图: {smoothed_plot_path} (存在: {os.path.exists(smoothed_plot_path)})"))
                
                if self.thread:
                    self.thread.quit()
                    self.thread.wait()
                self.worker = None
                self.thread = None

        # 运行GUI版本
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except ImportError:
        # 如果PyQt5不存在，运行命令行版本
        print("⚠️ PyQt5 未安装，运行命令行版本...")
        main()