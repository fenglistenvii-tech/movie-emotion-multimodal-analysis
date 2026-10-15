# Release 附件分发说明（测试数据 + 运行环境）

本仓库**只放代码与说明**。另外两类内容体积过大，通过 **GitHub Releases** 附件分发：

| 附件 | 内容 | 压缩后 |
| --- | --- | --- |
| `multimodal-emotion-results.7z` | 三组实验运行结果全量，含 1641 张 4K 抽帧图 | **1.25 GB** |
| `multimodal-emotion-results-lite.7z` | 只要 CSV / xlsx / 情感时间线图，不含抽帧图 | **11 MB** |
| `ffmpeg-2026-03-09-full-win64.7z` | `ffmpeg.exe` + `ffprobe.exe` + 环境说明 | **127 MB** |

这三个附件**已经用本机 7-Zip 24.09 打包好并做过 CRC 完整性校验**，就在 `F:\` 根目录下，
发布 Release 时直接拖进去即可。

这样做的原因：

- `ffmpeg.exe`（212.97 MB）与 `ffprobe.exe`（212.78 MB）都超过 GitHub 单文件 100 MB 硬上限，
  直接被仓库拒收；
- 抽帧图单张平均约 900 KB，1641 张合计约 1.28 GB，放进仓库会让 `clone` 变得很慢；
- GitHub 单个 Release 附件可到 2 GB，1.25 GB 的包没问题；
- 抽帧图可由 `src/` 下的脚本用原片重新生成，属于「可再生资产」，不适合纳入版本控制。

---

## 一、已打好的包（无需重做）

| 文件 | 大小 | 内容校验 |
| --- | --- | --- |
| `F:\multimodal-emotion-results.7z` | 1.25 GB | 1674 个文件（含 1641 张 `frame_*.jpg`）+ 12 个目录 |
| `F:\multimodal-emotion-results-lite.7z` | 11 MB | 33 个文件：9 个 CSV、9 个 xlsx、12 个 PNG、3 个 README |
| `F:\ffmpeg-2026-03-09-full-win64.7z` | 127 MB | `ffmpeg.exe`、`ffprobe.exe`、`环境依赖说明.md` |

> 之所以做成 `.7z` 而不是 `.zip`：`ffmpeg.exe` 与 `ffprobe.exe` 里约 90% 是相似内容，
> 7z 的固实压缩把 426 MB 压到了 127 MB；zip 做不到这一点。Windows 10（1803 以后）与
> Windows 11 已内置 7z 支持，双击即可打开。

如果你想自己重新打包，命令如下。

### 完整包

```powershell
& 'D:\7-Zip\7z.exe' a -t7z -mx=1 -mmt=on "F:\multimodal-emotion-results.7z" "F:\movie-emotion-multimodal-analysis\results\*"
```

> 4K JPEG 已经压缩过，`-mx=1` 就够；用 `-mx=9` 只会多花好几倍时间、体积几乎不变。

### 轻量包（不含 `frames/`）

```powershell
$tmp = 'F:\lite-pack'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
foreach ($ds in Get-ChildItem -LiteralPath 'F:\movie-emotion-multimodal-analysis\results' -Directory) {
    $dst = Join-Path $tmp $ds.Name
    New-Item -ItemType Directory -Path $dst | Out-Null
    Get-ChildItem -LiteralPath $ds.FullName -File | Copy-Item -Destination $dst
    foreach ($sub in @('完整数据','局部数据')) {
        $s = Join-Path $ds.FullName $sub
        if (Test-Path -LiteralPath $s) { Copy-Item -LiteralPath $s -Destination $dst -Recurse }
    }
}
& 'D:\7-Zip\7z.exe' a -t7z -mx=5 -mmt=on "F:\multimodal-emotion-results-lite.7z" "$tmp\*"
Remove-Item -LiteralPath $tmp -Recurse -Force
```

### ffmpeg 运行环境包

```powershell
$tmp = 'F:\ffmpeg-pack'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
Copy-Item 'F:\movie-emotion-multimodal-analysis\src\ffmpeg.exe','F:\movie-emotion-multimodal-analysis\src\ffprobe.exe' -Destination $tmp
Copy-Item 'F:\movie-emotion-multimodal-analysis\docs\环境依赖说明.md' -Destination $tmp
& 'D:\7-Zip\7z.exe' a -t7z -mx=1 -mmt=on "F:\ffmpeg-2026-03-09-full-win64.7z" "$tmp\*"
Remove-Item -LiteralPath $tmp -Recurse -Force
```

**所有包都生成在仓库目录之外**（`F:\` 根目录），这样绝不会被 `git add` 收进去。
打完可以用 `git -C "F:\movie-emotion-multimodal-analysis" status --short` 确认仓库仍然干净。

### 校验包是否完整

```powershell
& 'D:\7-Zip\7z.exe' t "F:\multimodal-emotion-results.7z"        # 结尾应显示 Everything is Ok
```

---

## 二、发布 Release

1. 打开仓库页面 → 右侧 **Releases** → **Create a new release**；
   或直接访问 `https://github.com/你的用户名/仓库名/releases/new`。
2. **Choose a tag**：输入 `v1.0-testdata`，点 **Create new tag on publish**。
3. **Release title**：`测试数据 + 运行环境（ffmpeg）`。
4. **Describe this release**：把下面这段贴进去（可按需修改）。

   ````markdown
   ## 测试数据

   三组影片的完整运行结果，解压后得到 `results/` 目录。

   | 目录 | 影片 | 局部精读区间 |
   | --- | --- | --- |
   | Titanic.Dataset_泰坦尼克号 | 《泰坦尼克号》Titanic (1997) | 第 531 ~ 563 帧 |
   | Your.Name.Dataset_你的名字 | 《你的名字。》Your Name. (2016) | 第 151 ~ 173 帧 |
   | The.Lychee.Road.Dataset_长安的荔枝 | 《长安的荔枝》The Lychee Road (2025) | 第 370 ~ 403 帧 |

   - `multimodal-emotion-results.7z`（1.25 GB）：全量，含 `dataset*.csv`、`*.xlsx` 汇总表、
     情感时间线 PNG，以及 1641 张抽帧图。
   - `multimodal-emotion-results-lite.7z`（11 MB）：轻量版，只含 CSV / xlsx / 情感时间线图。

   字段含义、目录结构与已知问题见仓库内 `docs/数据说明.md`。

   ## 运行环境

   `ffmpeg-2026-03-09-full-win64.7z`（127 MB）内含 `ffmpeg.exe` 与 `ffprobe.exe`
   （full build 2026-03-09-git-9b7439c31b，静态链接，支持 srt / ass / ssa / PGS 等字幕格式）。
   只有 `src/extract_subtitles.py` 需要它们：解压后放进 `src/` 目录即可。
   详细说明见仓库内 `docs/环境依赖说明.md`。

   两个 exe 来自 <https://www.gyan.dev/ffmpeg/builds/>，FFmpeg 为 LGPL/GPL 许可，
   本 Release 仅因本项目运行需要而原样附带。

   ## 版权

   不含任何影片文件。视频版权归各自权利人所有，此处仅用于学术研究与教学演示。
   ````

5. **Attach binaries**：三个 `.7z` 依次拖进去。1.25 GB 那个上传最慢，可能要几十分钟到一两个小时，
   取决于上行带宽；另两个很快。建议**先传小的两个**，再传大的，避免页面超时白等。
6. 点 **Publish release**。

---

## 三、README 里怎么引用

主 `README.md` 的「快速开始」与「测试结果（Releases）」两节已写好入口，格式如下
（把用户名和仓库名换成你自己的）：

```markdown
测试数据与 ffmpeg 运行环境都不在仓库中，请到
[Releases](https://github.com/你的用户名/仓库名/releases) 下载：

- `multimodal-emotion-results.7z` —— 三组实验运行结果（1.25 GB，含抽帧图）
- `multimodal-emotion-results-lite.7z` —— 只要图表数值（11 MB）
- `ffmpeg-2026-03-09-full-win64.7z` —— ffmpeg.exe + ffprobe.exe（127 MB）
```
