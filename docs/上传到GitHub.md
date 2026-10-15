# 上传到 GitHub 完整步骤

> 本仓库目录：`F:\movie-emotion-multimodal-analysis`
> 仓库状态：已 `git init`，分支 `main`，16 个文件已暂存（0.86 MB），提交身份已配置。
> 三个 Release 附件已用 7-Zip 打好，放在 `F:\` 根目录。

---

## 第 0 步：当前状态

| 项目 | 状态 |
| --- | --- |
| 仓库目录 | `F:\movie-emotion-multimodal-analysis` |
| 待提交内容 | 16 个文件 / 0.86 MB（源码、字幕、说明文档、LICENSE） |
| 提交身份 | 已在 git 全局配置里 |
| `.gitignore` | 已排除 `ffmpeg.exe`、`results/`、`_backup_meta/`、论文 docx/pdf、临时脚本，并实测校验 |
| Release 附件 | `F:\multimodal-emotion-results.7z`（1.25 GB）、`...-lite.7z`（10.58 MB）、`F:\ffmpeg-2026-03-09-full-win64.7z`（126.77 MB） |

---

## 第 1 步：在 GitHub 创建公开仓库

打开 <https://github.com/new>：

| 项目 | 填什么 |
| --- | --- |
| Repository name | `movie-emotion-multimodal-analysis` |
| Description | `融合多模态信息的影视作品情感计算与鉴赏研究 —— 本科毕业设计` |
| 可见性 | **Public** |
| Add a README file | **不勾选** |
| Add .gitignore | **None** |
| Choose a license | **None**（仓库里已经放好了 MIT 的 `LICENSE`） |

> **不要**勾 "Add a README file"：否则远端会先有一个提交，推送时会出现
> `rejected` 或 `refusing to merge unrelated histories`。

---

## 第 2 步：提交到本地

```powershell
git -C "F:\movie-emotion-multimodal-analysis" add -A
git -C "F:\movie-emotion-multimodal-analysis" commit -m "毕业设计：融合多模态信息的影视作品情感计算与鉴赏研究"
```

确认分支名是 `main`：

```powershell
git -C "F:\movie-emotion-multimodal-analysis" branch --show-current
```

若输出 `master`，执行 `git -C "F:\movie-emotion-multimodal-analysis" branch -M main`。

---

## 第 3 步：关联远端并推送

```powershell
git -C "F:\movie-emotion-multimodal-analysis" remote add origin https://github.com/你的用户名/movie-emotion-multimodal-analysis.git
git -C "F:\movie-emotion-multimodal-analysis" remote -v
git -C "F:\movie-emotion-multimodal-analysis" push -u origin main
```

### 登录方式

- **推荐**：弹窗里选 `Sign in with your browser`，浏览器点授权，凭据会被记住。
- 若要输**密码**：GitHub 已禁用账号密码，必须用 **Personal Access Token（PAT）**——
  <https://github.com/settings/tokens> → `Generate new token (classic)` → 勾选 **`repo`**
  → Generate → 复制 `ghp_...`（离开页面就看不到了），在密码栏粘贴这串 token。

推送成功的标志是输出末行出现 `* [new branch] main -> main`。

---

## 第 4 步：发布 Release（上传三个附件）

1. 打开 `https://github.com/你的用户名/movie-emotion-multimodal-analysis/releases/new`
2. **Choose a tag** 填 `v1.0-testdata`，点 **Create new tag on publish**
3. **Release title** 填 `测试数据 + 运行环境（ffmpeg）`
4. **Describe this release** 粘贴下面这段：

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
   - `multimodal-emotion-results-lite.7z`（10.58 MB）：轻量版，只含 CSV / xlsx / 情感时间线图。

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

5. **Attach binaries**：把三个 `.7z` 拖进去。**建议先拖两个小的**（10.58 MB、126.77 MB），
   再拖 1.25 GB 那个；大包上传可能几十分钟到一两个小时，期间别关页面。
6. 点 **Publish release**。

### 附件校验值（可选，写进 Release 说明供下载者核对）

| 文件 | 大小 | SHA256 |
| --- | --- | --- |
| `multimodal-emotion-results.7z` | 1,340,936,852 字节 | `535FCE855D81EBDF4737FE34BF1D093AC7A71514DCD69BD2CB69B0653B55379A` |
| `multimodal-emotion-results-lite.7z` | 11,096,136 字节 | `24E151CFA6C72B4AEC794A068615AB587E257DDD57C62C724E0601B69FDDA203` |
| `ffmpeg-2026-03-09-full-win64.7z` | 132,929,190 字节 | `C13C9A162BF798B79C6953205DA12CD23BF3DB037A7DD447AD15E145374110EF` |

---

## 第 5 步：上传后核对

- [ ] 首页 `README.md` 渲染正常（目录、表格、流程图代码块都在）
- [ ] 仓库名右侧显示 **Public**
- [ ] `src/` 有 4 个 `.py` + `blaze_face_short_range.tflite`，**没有** `ffmpeg.exe`
- [ ] `data/subtitles/` 有 3 个 `.srt`
- [ ] `docs/数据说明.md`、`docs/环境依赖说明.md`、`RELEASES.md`、`LICENSE` 都在
- [ ] **没有** `results/`、`ffmpeg.exe`、任何 `.pdf` / `.docx`
- [ ] Releases 里有 `v1.0-testdata` 与三个 `.7z` 附件
- [ ] 仓库体积在 1 MB 以内

```powershell
git -C "F:\movie-emotion-multimodal-analysis" status
```

预期 `nothing to commit, working tree clean`。

---

## 第 6 步：日常更新

```powershell
git -C "F:\movie-emotion-multimodal-analysis" add -A
git -C "F:\movie-emotion-multimodal-analysis" commit -m "说明这次改了什么"
git -C "F:\movie-emotion-multimodal-analysis" push
```

---

## 常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `remote origin already exists` | 重复 `remote add` | `git -C "..." remote set-url origin <地址>` |
| `rejected` / `failed to push some refs` | 远端有本地没有的提交 | `git -C "..." pull --rebase origin main` 后再 push |
| `refusing to merge unrelated histories` | 两条无关历史 | 加 `--allow-unrelated-histories` 再 pull |
| `src refspec main does not match any` | 还没 commit | 先做第 2 步 |
| `Authentication failed` | 用了账号密码 | 改用 PAT；或 `git config --global --unset credential.helper` 后重试 |
| `remote: error: File ... exceeds 100.00 MB` | 大文件被提交了 | 见下方「大文件已提交」 |
| 中文文件名显示成 `\346\226\207` | 未关闭 quotepath | `git config --global core.quotepath false` |

### 大文件已提交怎么办

**还没推送**：

```powershell
git -C "F:\movie-emotion-multimodal-analysis" rm -r --cached "路径/大文件.exe"
git -C "F:\movie-emotion-multimodal-analysis" commit --amend --no-edit
```

**已经推送**：光删文件不够，历史里仍有数据。最省事是 `Settings → Danger Zone →
Delete this repository` 删掉仓库，确认 `.gitignore` 生效后重建再推。

---

## 附：排除策略速查

| 内容 | 是否入库 | 原因 |
| --- | --- | --- |
| `src/*.py` + `.tflite` | ✅ | 核心成果 |
| `data/subtitles/*.srt` | ✅ | 共约 0.56 MB，复现分析必需 |
| `docs/`、`RELEASES.md`、`LICENSE` | ✅ | 说明与许可 |
| `results/`（含 1641 张抽帧图） | ❌ | 约 1.29 GB，改由 Release 分发 |
| `src/ffmpeg.exe` / `ffprobe.exe` | ❌ | 213 MB / 212.8 MB，超单文件 100 MB 上限 |
| 影片 `.mkv` / `.mp4` | ❌ | 版权 + 单个 20~60 GB |
| 论文 `.docx` / `.pdf` | ❌ | 个人答辩材料，未上传 |
