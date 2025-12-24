# 文档构建：TritonSurvey（latexmk + Makefile）

本目录是一个独立的 LaTeX 文档子工程，所有构建产物统一输出到 `docs/build/`。

## 环境要求

- 安装 TeX 发行版，并确保 `latexmk` 在 PATH 中（TeX Live 或 MiKTeX）
- Linux/macOS：需要 GNU Make（`make`）
- Windows：可选安装 GNU Make；如果没有 `make`，也可以直接使用 `.\build`

## 常用命令

先切换到 `docs/` 目录，再运行以下命令。

### Linux/macOS（或 Windows 已安装 `make`）

- 日常编译（默认安静）：`make`
- 草稿模式（图片占位加速）：`make draft`（**草稿模式只支持单主文件工程：`docs/` 顶层只能存在一个入口 `*.tex`；辅助 `.tex` 请放到 `sections/`**）
- 查错编译（输出更详细）：`make debug`
- 清理中间文件（保留 PDF）：`make clean`
- 完全清理（包含 PDF）：`make distclean`
- 需要 minted / 开启 `-shell-escape`：`make SHELL_ESCAPE=1`
- 切换引擎（例如 LuaLaTeX）：`make ENGINE=lualatex`

### Windows（没有 `make`）

在 `docs\` 目录下运行：

- 日常编译（默认安静）：`.\build`
- 草稿模式（图片占位加速）：`.\build draft`（**草稿模式只支持单主文件工程：`docs/` 顶层只能存在一个入口 `*.tex`；辅助 `.tex` 请放到 `sections/`**）
- 查错编译：`.\build debug`
- 草稿查错编译：`.\build draftdebug`
- 清理中间文件（保留 PDF）：`.\build clean`
- 完全清理（包含 PDF）：`.\build distclean`
- 打开 PDF：`.\build view`

可选参数（在 `cmd.exe` 中设置环境变量）：

- 需要 minted / 开启 `-shell-escape`：
  - `set SHELL_ESCAPE=1` 然后执行 `.\build`
- 切换引擎：
  - `set ENGINE=lualatex` 然后执行 `.\build`

PowerShell（VSCode 终端常见）对应写法：

- 需要 minted / 开启 `-shell-escape`：`$env:SHELL_ESCAPE=1; .\build`
- 切换引擎：`$env:ENGINE="lualatex"; .\build`

## 统计报告

每次成功构建都会生成一份简要的文档统计报告：

- 汇总：`docs/build/doc-report.txt`
- 分节统计：`docs/build/doc-report-sections.txt`

统计基于源码的启发式分析（非 PDF 精确统计）。若未安装 Python，将跳过报告生成。

## 说明

- 编译错误会以 `file:line` 形式输出（`-file-line-error`），便于编辑器跳转定位。
- `docs/latexmkrc` 为可选配置；主要构建参数由 `Makefile` / `.\build` 控制。
- `debug` / `draftdebug`：关闭 `-silent`，使用 `-interaction=errorstopmode -halt-on-error -file-line-error`，便于快速定位报错（必要时可直接打开 `build/*.log`）。
- 草稿模式会在 `build/` 下自动生成一个 `*-draft.tex` 包装文件（不应提交到 git）。
