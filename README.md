# 融合多模态信息的影视作品情感计算与鉴赏研究

> 本科毕业设计 · 多模态情感分析工具
> 以电影为对象，抽取 **画面（视觉表情）+ 台词字幕（中文文本情感）** 两路信息，按时间轴对齐后计算情感曲线，为影视作品的鉴赏与叙事节奏分析提供量化依据。

---

## 目录

- [一、项目简介](#一项目简介)
- [二、快速开始](#二快速开始)
- [三、方法流程](#三方法流程)
- [四、仓库结构](#四仓库结构)
- [五、环境配置](#五环境配置)
- [六、数据准备](#六数据准备)
- [七、运行方法](#七运行方法)
- [八、输出说明](#八输出说明)
- [九、测试结果（Releases）](#九测试结果releases)
- [十、已知问题与注意事项](#十已知问题与注意事项)
- [验证状态](#验证状态)
- [十一、版权、许可与致谢](#十一版权许可与致谢)

---

## 一、项目简介

传统影视鉴赏多依赖主观文字评论，缺少可复现的量化手段。本项目把「多模态情感计算」引入影视鉴赏场景，在同一时间轴上融合两类信号：

| 模态 | 数据来源 | 分析方法 | 输出指标 |
| --- | --- | --- | --- |
| 文本模态 | 影片内嵌字幕 / 外挂 `.srt` | SnowNLP 中文情感分析 | `text_sentiment_score`（0~1，0.5 为中性） |
| 视觉模态 | 抽帧画面中的人脸 | DeepFace 表情识别 | `happy`、`sad`（0~100 概率）、`dominant_visual_emotion` |

两路信号按秒级时间戳对齐、做滑动窗口平滑后，绘制**情感时间线**（原始数据图 + 平滑趋势图），用于观察影片情绪的起伏与高潮段落。

技术亮点：

- **人脸门控抽帧**：先用 MediaPipe BlazeFace 检测人脸，只保留「有人脸」的帧，避免空镜头污染视觉情感统计，同时把 4K 画面缩放到 320px 再检测以提升速度。
- **多线程流水线**：读取帧 / 人脸检测 / 字幕匹配与落盘三段线程用队列解耦，抽帧速度显著优于逐帧串行处理。
- **可视化工具**：PyQt5 图形界面把「抽帧对齐」和「情感分析」两步串起来，支持指定帧区间做局部情节的精读分析。

---

## 二、快速开始

**本仓库只包含代码与说明，不包含测试数据。**

```bash
# 1. 取代码
git clone https://github.com/fenglistenvii-tech/movie-emotion-multimodal-analysis.git
cd movie-emotion-multimodal-analysis

# 2. 装依赖（Python 3.9 ~ 3.12）
pip install -r requirements.txt

# 3. 准备 ffmpeg：下载后把 ffmpeg.exe、ffprobe.exe 放到 src/ 目录下
#    https://www.gyan.dev/ffmpeg/builds/   （详见第五节）

# 4. 跑起来
cd src
python main_ui.py            # 图形界面
```

**测试数据（三组影片的完整运行结果）请到 Releases 下载：**

> [Releases](https://github.com/fenglistenvii-tech/movie-emotion-multimodal-analysis/releases)
> → 全量包：下载 `multimodal-emotion-results-split-001.7z` / `-002.7z` / `-003.7z` **三个分卷**，
>   放到同一目录后改名回 `.7z.001` / `.7z.002` / `.7z.003`，
>   再右键点 `.001` 用 7-Zip 解压（自动连读后续分卷），得到 `.7z` 后再解压一次即得 `results/`
> → 或只下 `multimodal-emotion-results-lite.7z`（10.58 MB，仅图表数据，不含抽帧图）

也可只下载分析结果（`multimodal-emotion-results-lite.7z`，10.58 MB，含 CSV / xlsx / 情感时间线图）而不含抽帧图。

> **具体怎么用（从安装到看懂输出）见 [`docs/使用说明.md`](docs/使用说明.md)。**
> 字段含义、目录结构与已知问题见 [`docs/数据说明.md`](docs/数据说明.md)；
> ffmpeg 配置细节见 [`docs/环境依赖说明.md`](docs/环境依赖说明.md)。

---

## 三、方法流程

```
                    ┌──────────────────────────────┐
   MKV 影片 ───────▶ │ ① 字幕流探测与提取            │ ────▶  .srt 字幕
                    │   ffprobe + ffmpeg           │
                    └──────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
   MKV 影片 ───────▶ │ ② 人脸门控抽帧 + 字幕对齐      │ ────▶  frames/*.jpg
                    │   OpenCV + MediaPipe BlazeFace│        dataset.csv
                    └──────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ ③ 多模态情感计算              │ ────▶  dataset_full_analysis.csv
                    │   SnowNLP(文本) + DeepFace(画面)│       dataset_some_analysis.csv
                    │   + 滑动窗口平滑 + 绘图        │       emotion_timeline_*.png
                    └──────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ ④ PyQt5 图形界面（可选）       │
                    └──────────────────────────────┘
```

---

## 四、仓库结构

```
.
├── src/                           # 全部源码
│   ├── extract_subtitles.py       # ① 从 MKV 中探测并提取字幕
│   ├── extract_frames.py          # ② 人脸门控抽帧 + 字幕时间对齐
│   ├── analyze_emotions.py        # ③ 文本 + 视觉情感分析与绘图
│   ├── main_ui.py                 # ④ PyQt5 图形界面主程序
│   └── blaze_face_short_range.tflite   # BlazeFace 人脸检测模型（224 KB，已入库）
│
├── data/subtitles/                # 三部影片的字幕（各一两百 KB，已入库）
│
├── docs/
│   ├── 使用说明.md                 # 怎么用：安装、运行、看懂输出、常见问题
│   ├── 数据说明.md                 # Release 数据包的目录结构、字段含义与已知问题
│   └── 环境依赖说明.md              # ffmpeg / ffprobe 的用途、版本与配置方式
│
├── RELEASES.md                    # 如何把测试数据与 ffmpeg 打包上传到 GitHub Releases
├── LICENSE                        # MIT 许可证（含影片版权补充说明）
├── requirements.txt
├── .gitignore
├── .gitattributes
└── README.md
```

仓库里**没有**论文、工具说明书 PDF 与影片文件；三组实验的运行结果（`results/`）也不在仓库中，
而是作为 Release 附件分发，原因与体积：

| 内容 | 体积 | 位置 |
| --- | --- | --- |
| 源码 + 说明 + 字幕 | 约 0.3 MB | 本仓库 |
| 分析结果（CSV / xlsx / 时间线 PNG） | 11 MB | Release（轻量包） |
| 抽帧图 1641 张（4K 截图，平均 900 KB/张） | 约 1.28 GB | Release（完整包） |
| 原片 MKV | 单个 20~60 GB | 不提供（版权 + 体积） |

Release 数据包的内部结构：

```
results/
├── Titanic.Dataset_泰坦尼克号/
├── Your.Name.Dataset_你的名字/
└── The.Lychee.Road.Dataset_长安的荔枝/
        ├── dataset.csv                 # 抽帧记录（extract_frames.py）
        ├── dataset_full_analysis.csv   # 全片情感分析（analyze_emotions.py）
        ├── dataset_some_analysis.csv   # 区间情感分析（analyze_emotions.py）
        ├── frames/                     # 抽帧图像
        ├── 完整数据/                    # 全片汇总 xlsx + 时间线图
        └── 局部数据/                    # 局部精读 xlsx + 时间线图
```

> 最初整理时用的是「4-毕业论文 / 8-附加」这种毕业设计递交编号，在 GitHub 上没有意义，已改为上表的通用结构；数据集目录名也已带上电影名。
>
> 四个脚本原先名为 `1_prepare_dataset.py` / `2_extract_subtitles.py` / `3_analyze_emotions_range.py` / `4_main_ui_range.py`，前两个的名称与实际功能不符（实际是「字幕提取」和「抽帧对齐」），现已按实际功能重命名。

---

## 五、环境配置

**Python 版本**：3.9 ~ 3.12。本仓库的代码已在本机 **Python 3.12.10** 环境下实测跑通（见文末[验证状态](#验证状态)）。

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

# 2. 安装依赖
pip install -r requirements.txt
```

**ffmpeg 外部依赖**（只有 `extract_subtitles.py` 需要）：

1. 从 <https://www.gyan.dev/ffmpeg/builds/> 下载 `ffmpeg-release-essentials.zip`；
2. 解压后把 `ffmpeg.exe`、`ffprobe.exe` 复制到 `src/` 目录下（脚本会优先使用同目录的这两个文件），或加入系统 `PATH`。

**DeepFace 权重**：首次运行 `analyze_emotions.py` 时，DeepFace 会自动下载约 200MB 的人脸检测 / 表情识别权重到用户目录（`.deepface/`），需要联网，请耐心等待。这些权重已加入 `.gitignore`，不会也不应上传。

---

## 六、数据准备

### 6.1 实验影片

实验使用三部影片（4K 原盘 MKV）：

| 影片 | 说明 |
| --- | --- |
| 《泰坦尼克号》Titanic (1997) | 经典灾难爱情片，情绪起伏剧烈 |
| 《你的名字。》Your Name. (2016) | 动画电影，情绪线细腻 |
| 《长安的荔枝》The Lychee Road (2025) | 国产影片，用于验证方法在当代作品上的表现 |

> 影片本体受版权保护且单个 20~60 GB，**未包含在本仓库中**，也不随 Release 分发。复现实验需自备合法来源的 MKV 文件。

### 6.2 字幕

若 MKV 内嵌文本字幕，直接用 `extract_subtitles.py` 提取；若为 PGS 图片字幕（脚本会明确提示 `⚠️图片格式(需OCR)`），需先经 OCR 转文本，或改用外挂 `.srt`。

三部影片用到的字幕已放在 `data/subtitles/`，可直接作为 `extract_frames.py` 的输入。

### 6.3 人脸检测模型

`blaze_face_short_range.tflite`（224 KB）已随仓库提供，位于 `src/`，脚本按当前工作目录查找该文件，因此请在 `src/` 目录下运行。

---

## 七、运行方法

### 方式 A：图形界面（推荐）

```bash
cd src
python main_ui.py
```

- **标签页 1「抽帧与字幕对齐」**：选择视频、字幕、输出目录，设置抽帧频率（默认 `0.2` 帧/秒，即每 5 秒一帧），点击「开始抽帧」。
- **标签页 2「情感分析」**：选择上一步的输出目录（应含 `dataset.csv` 和 `frames/`），可指定**起始帧 / 结束帧**做局部精读（结束帧填 `99999` 表示到片尾），点击「开始情感分析」，完成后界面直接显示两张情感时间线图。

若未安装 PyQt5，程序会自动回退到命令行菜单模式。

### 方式 B：分步命令行

```bash
cd src

# ① 探测并提取字幕：结果得到 <影片名>.chi.srt
python extract_subtitles.py

# ② 抽帧 + 字幕对齐：输出 <输出目录>/frames/ 与 <输出目录>/dataset.csv
python extract_frames.py <视频.mkv> <字幕.srt> <输出目录> [抽帧频率=0.2]

# ③ 全片情感分析（省略起止帧则分析全部）
python analyze_emotions.py <数据集目录>
python analyze_emotions.py <数据集目录> <起始帧> <结束帧>
```

> 三个脚本底部的 `MKV_FILE`、`video_path`、`dataset_root` 是你本机的绝对路径，**直接运行前请改成自己的路径**（脚本默认值仅作示例）。

---

## 八、输出说明

### 8.1 数据表字段

`dataset.csv`（抽帧阶段产出）：

| 字段 | 含义 |
| --- | --- |
| `id` | 保留下来的帧序号（从 0 开始） |
| `time` | 该帧在影片中的时间戳（秒） |
| `src_frame` | 原视频中的绝对帧号 |
| `img` | 图像相对路径，如 `frames/frame_00000.jpg` |
| `text` | 与该时间戳匹配的字幕文本（含 ASS 样式标签，分析时会自动清洗） |
| `faces` | 该帧检出的人脸数量 |

`dataset_full_analysis.csv` / `dataset_some_analysis.csv` 在此基础上追加：

| 字段 | 含义 |
| --- | --- |
| `text_sentiment_score` | SnowNLP 文本情感值（0~1，越接近 1 越正面） |
| `happy` / `sad` | DeepFace 输出的「高兴」「悲伤」概率（0~100） |
| `dominant_visual_emotion` | 该帧主导表情；异常时为 `No Face` / `Image Missing` |

### 8.2 图表

- `emotion_timeline_raw.png`：原始数据图，三条曲线为文本情感（归一化到 0~100）、视觉高兴、视觉悲伤，横轴按 `分:秒` 刻度。
- `emotion_timeline_smoothed.png`:平滑趋势图，对三个序列做窗口 `7`（中心对齐）的移动平均，用于观察整体情绪走向。

### 8.3 汇总表

`完整数据/初始数据.xlsx`、`完整数据/完整数据.xlsx` 与 `局部数据/局部数据（起止帧）.xlsx`，
是把流程产出的 CSV 数据转成 Excel 格式的版本（`.csv` 直接打开时中文与精度显示不佳），
分别对应抽帧记录、全片分析结果与区间分析结果，数值与同名 `.csv` 一致。转成 xlsx 是为了
查看方便、也便于答辩时取数制表。

> 注意：`完整数据/` 里放的是**全片**结果（`初始数据.xlsx` 与 `完整数据.xlsx`），
> `局部数据/` 里放的是**指定帧区间**的结果，两者不要混用。

---

## 九、测试结果（Releases）

三组实验的完整运行结果**不在仓库中**，而是作为 Release 附件分发：

| 附件 | 内容 | 体积 |
| --- | --- | --- |
| `multimodal-emotion-results-split-001.7z` / `-002.7z` / `-003.7z` | 三组结果全量，含 1641 张 4K 抽帧图（分 3 卷） | 共 1.25 GB |
| `multimodal-emotion-results-lite.7z` | 只含 CSV、xlsx 汇总表与情感时间线图 | 10.58 MB |
| `ffmpeg-2026-03-09-full-win64.7z` | `ffmpeg.exe` + `ffprobe.exe` + 环境说明 | 126.77 MB |

> **全量包怎么解压**：三个分卷都要下载，放到同一目录后改名回 `.7z.001` / `.7z.002` / `.7z.003`
> （GitHub 不接受 `.001` 这类扩展名，所以上传时改成了 `-001.7z`），然后右键点 `.001` 用 7-Zip
> 解压，会自动连读后续分卷；解出来的还是一个 `.7z`，**再解压一次**才是 `results/` 目录。
>
> 改名命令（在下载目录里执行即可）：
>
> ```powershell
> 1..3 | ForEach-Object {
>     Rename-Item "multimodal-emotion-results-split-00$_.7z" "multimodal-emotion-results-split.7z.00$_"
> }
> ```
>
> 只要图表数值的话，下载 10.58 MB 的轻量包即可，不必碰分卷。

下载地址：<https://github.com/fenglistenvii-tech/movie-emotion-multimodal-analysis/releases>

| 数据集 | 对应影片 | 全片分析 | 局部精读区间 |
| --- | --- | --- | --- |
| `Titanic.Dataset_泰坦尼克号` | 《泰坦尼克号》Titanic (1997) | ✅ | 第 531 ~ 563 帧 |
| `Your.Name.Dataset_你的名字` | 《你的名字。》Your Name. (2016) | ✅ | 第 151 ~ 173 帧 |
| `The.Lychee.Road.Dataset_长安的荔枝` | 《长安的荔枝》The Lychee Road (2025) | ✅ | 第 370 ~ 403 帧 |

解压后得到 `results/` 目录即可直接使用；字段含义、目录结构、字幕广告清理带来的
数值变化等细节，见 [`docs/数据说明.md`](docs/数据说明.md)。
若想自己重新打包 Release，见 [`RELEASES.md`](RELEASES.md)。

**ffmpeg / ffprobe 也在这个 Release 里**：`ffmpeg.exe`（213 MB）与 `ffprobe.exe`（212.8 MB）
超过 GitHub 单文件 100 MB 上限，无法放进仓库，因此作为附件分发。只有
`extract_subtitles.py` 需要它们，解压后放进 `src/` 目录即可，详见
[`docs/环境依赖说明.md`](docs/环境依赖说明.md)。

> 抽帧图之所以不放仓库：单张平均约 900 KB（4K 截图），1641 张合计约 1.28 GB，
> 放进仓库会让 `clone` 变得很慢，而它们本来就能用 `extract_frames.py` 从原片重新生成。

---

## 十、已知问题与注意事项

以下几处是整理仓库时发现的问题。前两条已通过**重命名脚本**修好，其余保留原实现并在此说明，便于对照论文提交版本。

1. ~~脚本文件名与实际功能不一致~~ —— **已修复**

   原 `1_prepare_dataset.py` 实现的是「字幕提取」，`2_extract_subtitles.py` 实现的是「抽帧与字幕对齐」，文件名与实际功能不符。现重命名为 `extract_subtitles.py`、`extract_frames.py`，与函数语义一致。

2. ~~`main_ui.py` 的模块导入名与仓库文件不一致~~ —— **已修复**

   该文件原本写的是：

   ```python
   from extract_subtitles import run_extract_subtitles
   from analyze_emotions_range import run_analyze_emotions
   ```

   而当时的实际文件名是 `2_extract_subtitles.py` 和 `3_analyze_emotions_range.py`，直接运行会 `ModuleNotFoundError`。
   重命名后第一条导入已经成立；第二条需把模块名改成 `analyze_emotions`（即原名 `3_analyze_emotions_range.py` 的文件，仓库中已重命名）。

3. ~~`main_ui.py` 命令行回退分支的参数顺序传错~~ —— **已修复**

   该分支原为 `run_analyze_emotions(dataset_dir, log_callback, start_idx, end_idx)`，但函数签名是 `run_analyze_emotions(dataset_root, start_idx=None, end_idx=None, log_callback=None)`，位置参数错位。现改为：

   ```python
   run_analyze_emotions(dataset_dir, start_idx, end_idx, log_callback)
   ```

   已用 AST 解析逐一核对，两处调用点（命令行分支与 GUI 分支）的实参顺序现在都正确。

4. ~~`extract_frames.py` 的 `run_extract_subtitles` 缺少 `log_callback` 默认值~~ —— **已修复**

   现签名为 `run_extract_subtitles(video_path, srt_path, output_dir, fps_target, log_callback=None)`，并在函数开头兜底 `if log_callback is None: log_callback = print`，因此可以脱离 GUI 独立调用。

5. **三个脚本底部硬编码了本机绝对路径**

   如 `E:\movie\...mkv`、`F:\Personal\Titanic.Dataset`。这些是开发时的示例路径，运行时必须替换为自己的路径。

6. **`dataset.csv` 的 `text` 字段保留 ASS 样式标签**

   如 `<font face="WenQuanYi Micro Hei" size="66">`。分析阶段会用正则清洗后再送入 SnowNLP，**因此情感计算结果不受影响**；只是原始 CSV 可读性较差，属正常现象。

7. **`*.xlsx` 的格式说明**

   这些汇总表由流程产出的数据转成 Excel 格式——`dataset.csv` 与 `dataset_*_analysis.csv` 直接用 Excel
   打开时中文与精度显示不佳，转成 `.xlsx` 便于查看与答辩取数。**数值与同名 `.csv` 一致**，
   个别单元格的数字格式略有差异（例如 `time` 列 CSV 写作 `546.0`、xlsx 显示为 `546`），不影响数据。

   三组结果的工作表名已统一为 `dataset` / `dataset_full_analysis` / `dataset_some_analysis`。

8. **字幕已做广告清理，时间戳未改动**

   三份字幕中被整条删除了片头的发行方署名与网址条目（《长安的荔枝》4 条、《你的名字。》1 条），删除时**只删整条、不改动其余条目的时间码**，因此字幕与抽帧图片的时间对齐关系保持不变。被删条目都位于影片开头 30 秒内；受影响的帧其 `text` 由广告文本变为空字符串，`text_sentiment_score` 相应变为中性值 `0.5`。

---

## 验证状态

本仓库源码在本机 **Python 3.12.10** 环境下做过一轮可运行性验证，结论如下：

| 检查项 | 方式 | 结果 |
| --- | --- | --- |
| 4 个脚本语法 | `py_compile` | ✅ 全部通过 |
| 模块导入链 | `import` 四个模块 | ✅ 全部通过（含 `main_ui` 的两条 import） |
| 调用点实参顺序 | AST 解析逐一核对 | ✅ 4 处调用点全部正确 |
| 字幕提取 `extract_subtitles.py` | 用 `ffmpeg` 现场封装一个含 SubRip 字幕流的容器并提取 | ✅ 探测到字幕流并成功导出 505 KB 的 `.srt` |
| 抽帧对齐 `extract_frames.py` | 真实电影片段 + 真实字幕，2 帧/秒 | ✅ 产出 342 行 `dataset.csv` 与 342 张图，行数与落盘数一致 |
| 文本情感 SnowNLP | 正/负面文本 + 空值 | ✅ 正面 0.90 > 负面 0.60，空值回退 0.5 |
| 视觉情感 DeepFace | 对真实抽帧逐帧分析 | ✅ 3/3 帧给出表情判定（happy 100.0 / fear 等） |
| BlazeFace 人脸检测 | 载入 `.tflite` 对真实抽帧推理 | ✅ 模型加载成功，检出 1 张人脸，与 `dataset.csv` 记录的 `faces=1` 一致 |
| PyQt5 界面 `main_ui.py` | offscreen 模式真实启动 `__main__` 入口 | ✅ 窗口 1000×800、73 个控件、18 个关键属性与 10 个槽函数齐全，事件循环正常 |
| ffmpeg / ffprobe | `-version` | ✅ 可执行（213 MB / 212.8 MB，full build） |
| `analyze_emotions.py` 端到端 | 真实数据切片跑完全流程 | ✅ 输出 CSV 与两张情感时间线图 |

> 说明：`results/` 中的 `完整数据.xlsx`、`局部数据（起止帧）.xlsx` 等汇总表，是把抽帧对齐与情感分析
> 产出的数据转成 Excel 格式的版本（原始 `.csv` 可读性差，转 xlsx 便于查看与答辩取数），数值与同名 `.csv` 一致。

---

## 十一、版权、许可与致谢

### 许可

本仓库中的**源代码与原创文档**采用 [MIT 许可证](LICENSE) 授权，可自由使用、修改与再分发，保留版权声明即可。

### 影片版权声明

- 本仓库与配套 Release **不包含任何影片文件**。
- 实验所用影片的版权归各自权利人所有。
- Release 中 `results/` 下的视频截图（`frames/`）**仅用于学术研究与教学演示**中的画面情感分析，**不得用于任何商业用途**，也不得再分发以替代观看原片。
- 仓库内收录的字幕体积很小（各一两百 KB），是复现分析所必需的输入。
- 若权利人认为使用不当，请通过 Issue 联系，我会立即移除相关内容。

### 第三方组件

| 组件 | 用途 | 许可 |
| --- | --- | --- |
| FFmpeg / ffprobe | 字幕流探测与提取 | LGPL / GPL（Release 中附带的构建为 GPL 版） |
| OpenCV | 视频抽帧 | Apache-2.0 |
| MediaPipe（BlazeFace） | 人脸检测 | Apache-2.0 |
| DeepFace | 表情识别 | MIT |
| SnowNLP | 中文文本情感 | MIT |
| PyQt5 | 图形界面 | GPL v3（仅界面部分使用；不使用界面可不安装） |
| pandas / Matplotlib | 数据处理与绘图 | BSD / PSF-based |

如对方法或代码有疑问，欢迎通过 Issue 交流。
