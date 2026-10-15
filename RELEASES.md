# Release 附件分发说明（测试数据 + 运行环境）

本仓库**只放代码与说明**。另外两类内容体积过大，通过 **GitHub Releases** 附件分发：

| 附件 | 内容 | 压缩后 |
| --- | --- | --- |
| `multimodal-emotion-results-split.7z.001` `.002` `.003` | 三组实验运行结果全量，含 1641 张 4K 抽帧图（分 3 卷） | **512 / 512 / 255 MB** |
| `multimodal-emotion-results-lite.7z` | 只要 CSV / xlsx / 情感时间线图，不含抽帧图 | **10.58 MB** |
| `ffmpeg-2026-03-09-full-win64.7z` | `ffmpeg.exe` + `ffprobe.exe` + 环境说明 | **126.77 MB** |

这四类文件**已经用本机 7-Zip 24.09 打包好并做过 CRC 完整性校验**，就在 `F:\` 根目录下，
发布 Release 时直接拖进去即可。

这样做的原因：

- `ffmpeg.exe`（212.97 MB）与 `ffprobe.exe`（212.78 MB）都超过 GitHub 单文件 100 MB 硬上限，
  直接被仓库拒收；
- 抽帧图单张平均约 900 KB，1641 张合计约 1.28 GB，放进仓库会让 `clone` 变得很慢；
- GitHub 单个 Release 附件可到 2 GB，1.25 GB 的包没问题；
- 抽帧图可由 `src/` 下的脚本用原片重新生成，属于「可再生资产」，不适合纳入版本控制。

---

## 一、已打好的包（无需重做）

| 文件 | 大小 | 内容 |
| --- | --- | --- |
| `F:\multimodal-emotion-results-split.7z.001` `.002` `.003` | 512 / 512 / 255 MB | 全量数据（1674 个文件，含 1641 张 `frame_*.jpg`），分 3 卷 |
| `F:\multimodal-emotion-results.7z` | 1.25 GB | 同上，**未分卷的原包**（内容与上面三卷完全等价，留作备份） |
| `F:\multimodal-emotion-results-lite.7z` | 10.58 MB | 33 个文件：9 CSV、9 xlsx、12 PNG、3 README，不含 `frames/` |
| `F:\ffmpeg-2026-03-09-full-win64.7z` | 126.77 MB | `ffmpeg.exe`、`ffprobe.exe`、`环境依赖说明.md` |

> **为什么大包要分卷**：GitHub 附件本身支持到 2 GB，但网页上传 1 GB 以上的文件经常超时失败
> （报 `Something went really wrong, and we can't process that file`）。拆成 512 MB 的分卷后
> 每个都能很快传完，断了也只需重传那一卷。
>
> 分卷是**只复制数据、不重新压缩**（`-mx=0`），所以三卷合起来与未分卷的原包字节等价：
> 已实测把三卷还原后得到与原包 **SHA256 完全相同**的文件。

### 分卷的 SHA256（可贴进 Release 说明供校验）

| 文件 | SHA256 |
| --- | --- |
| `multimodal-emotion-results-split.7z.001` | `83BD440BED76A1F527A0637DE501BDF8BB30225DB90BD3C18C466F4601362A1A` |
| `multimodal-emotion-results-split.7z.002` | `EFE4309E62F852B98E58E736FB03D362102F0CD644077C1D965AC38AD234D6D9` |
| `multimodal-emotion-results-split.7z.003` | `8C150887C072C1979A3E0787F3AA7DAF42936BCD06893B7DBDEB38B5039D88CE` |
| 三卷还原后的 `multimodal-emotion-results.7z` | `E24E57BF75EEF5BA2FF894D56AD1C7BA80825A22E30C96CB1D5143699067F9E6` |

### 下载者怎么用（写进 Release 说明）

1. 把 `.001`、`.002`、`.003` **三个卷都下载**到同一个目录；
2. 右键点 `.001` → 7-Zip → 解压（7-Zip 会自动连读 `.002`、`.003`）；
3. 得到 `multimodal-emotion-results.7z`，再解压一次就是 `results/` 目录。

> Windows 11 与 Win10 1803+ 已内置 7z 支持，双击 `.001` 也能打开。
> 只想要图表数值的话，直接下 10.58 MB 的轻量包，不用碰分卷。

### 如果还是传不上去

改用 GitHub CLI（支持大文件，能断点续传）：

```powershell
winget install --id GitHub.cli
gh auth login
gh release upload v1.0-testdata "F:\multimodal-emotion-results-split.7z.*"
```

**或干脆减小体积**：不再提供带全部抽帧图的完整包，只留轻量包（10.58 MB）；
抽帧图本来就能用 `extract_frames.py` 从原片重新生成，`docs/数据说明.md` 里有说明。

---

## 二、自己重新打包的命令

### 完整包

```powershell
& 'D:\7-Zip\7z.exe' a -t7z -mx=1 -mmt=on "F:\multimodal-emotion-results.7z" "F:\movie-emotion-multimodal-analysis\results\*"
```

> 4K JPEG 已经压缩过，`-mx=1` 就够；用 `-mx=9` 只会多花好几倍时间、体积几乎不变。

### 拆成 512 MB 分卷

```powershell
# 基于已打好的原包分卷（-mx=0 只复制数据，几秒钟完成）
& 'D:\7-Zip\7z.exe' a -t7z -mx=0 -v512m -mmt=on -y "F:\multimodal-emotion-results-split.7z" "F:\multimodal-emotion-results.7z"

# 校验三卷是否能正确连读
& 'D:\7-Zip\7z.exe' t "F:\multimodal-emotion-results-split.7z.001"
```

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
   或直接访问 `https://github.com/fenglistenvii-tech/movie-emotion-multimodal-analysis/releases/new`。
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

   - `multimodal-emotion-results-split.7z.001` / `.002` / `.003`（共 1.25 GB）：全量，
     含 `dataset*.csv`、`*.xlsx` 汇总表、情感时间线 PNG，以及 1641 张抽帧图。
     **三个分卷都要下载**，右键点 `.001` 用 7-Zip 解压（自动连读后续分卷），
     得到 `.7z` 后再解压一次即得 `results/` 目录。
   - `multimodal-emotion-results-lite.7z`（10.58 MB）：轻量版，只含 CSV / xlsx / 情感时间线图，
     不需要抽帧图的话只下这个就够。

   字段含义、目录结构与已知问题见仓库内 `docs/数据说明.md`。

   ## 运行环境

   `ffmpeg-2026-03-09-full-win64.7z`（126.77 MB）内含 `ffmpeg.exe` 与 `ffprobe.exe`
   （full build 2026-03-09-git-9b7439c31b，静态链接，支持 srt / ass / ssa / PGS 等字幕格式）。
   只有 `src/extract_subtitles.py` 需要它们：解压后放进 `src/` 目录即可。
   详细说明见仓库内 `docs/环境依赖说明.md`。

   两个 exe 来自 <https://www.gyan.dev/ffmpeg/builds/>，FFmpeg 为 LGPL/GPL 许可，
   本 Release 仅因本项目运行需要而原样附带。

   ## 版权

   不含任何影片文件。视频版权归各自权利人所有，此处仅用于学术研究与教学演示。
   ````

5. **Attach binaries**：按下面顺序拖进去，**先小后大**，避免页面超时白等：

   | 顺序 | 文件 | 大小 |
   | --- | --- | --- |
   | 1 | `multimodal-emotion-results-lite.7z` | 10.58 MB |
   | 2 | `ffmpeg-2026-03-09-full-win64.7z` | 126.77 MB |
   | 3~5 | `multimodal-emotion-results-split.7z.001` / `.002` / `.003` | 512 / 512 / 255 MB |

   > 分卷每个都不大，传完一卷再传下一卷；哪一卷失败就单独重传那一卷。
   > 不要再尝试整包 1.25 GB 直接上传——网页端会超时失败。

6. 点 **Publish release**。

---

## 三、README 里怎么引用

主 `README.md` 的「快速开始」与「测试结果（Releases）」两节已按分卷方案写好入口，
内容如下：

```markdown
测试数据与 ffmpeg 运行环境都不在仓库中，请到
[Releases](https://github.com/fenglistenvii-tech/movie-emotion-multimodal-analysis/releases) 下载：

- `multimodal-emotion-results-split.7z.001~003` —— 三组实验运行结果（共 1.25 GB，含抽帧图，
  三个分卷都要下，右键点 .001 解压）
- `multimodal-emotion-results-lite.7z` —— 只要图表数值（10.58 MB）
- `ffmpeg-2026-03-09-full-win64.7z` —— ffmpeg.exe + ffprobe.exe（126.77 MB）
```
