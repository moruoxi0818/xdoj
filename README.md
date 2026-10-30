# XDOJ 自动刷题 · 开发说明

> 只想用软件的话，请直接看 **[使用说明.md](使用说明.md)**，双击 `启动.bat` 即可。

## 下载现成程序

不想装 Python 的话，直接用打包好的单文件版（就是桌面上的 `XDOJ自动刷题.exe`，上传时改名为 `XDOJ-Auto.exe`）：

- [XDOJ-Auto.exe 直接下载](https://github.com/moruoxi0818/xdoj/releases/download/v1.1.0/XDOJ-Auto.exe) —— 双击即用，首次运行会在同目录生成 `.env`，按页面提示填学号、密码、AI Key。
- [全部版本（Release 页）](https://github.com/moruoxi0818/xdoj/releases)

> 文件约 108 MB，超过了 GitHub 单文件 100 MB 的上限，所以放在 Release 里而不是直接提交进仓库。
> 单文件版仍然需要本机装有 g++，见下面「编译环境（重要）」，否则本地编译校验会失败。

指定**考试编号**和**题目编号**，点一下「执行」就自动完成：

```
下载题面 PDF → 抽文字与样例 → 大模型出码 → 本地 g++ 编译
→ 样例自检 → 提交 → 轮询判定 → 失败带着错误重做
```

## 运行方式

| 方式 | 命令 | 说明 |
| --- | --- | --- |
| 一键启动（推荐） | 双击 `启动.bat` | 自动建 `.venv`、装依赖、起服务、开浏览器 |
| 手动起服务 | `.venv\Scripts\python.exe server.py` | 端口自动从 8000 往后找，真实端口写在 `port.txt` |
| 命令行批跑 | `.venv\Scripts\python.exe auto.py --contest 310 --problem 509` | 支持 `--range 39-44`、`--all`、`--list`、`--dry` |

## 首次配置

程序**不内置任何账号和密钥**。首次打开页面会弹出配置向导，填写：

- 学号 / 密码：登录 XDOJ 用
- AI API Key：智谱开放平台 https://open.bigmodel.cn 申请
- 模型默认 `glm-4.5-flash`，接口地址默认智谱 v4 端点

保存后写入同目录 `.env`（首次运行从 `.env.example` 生成），也可以在 `.env` 里手工填：

```
AI_API_KEY=你自己的Key
AI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
AI_MODEL=glm-4.5-flash
AI_FALLBACK_MODEL=glm-4-flash
AI_MAX_TOKENS=4096

XDOJ_USER=你的学号
XDOJ_PASS=你的密码
```

`.env` 只在本机，不要提交到仓库、不要随包分发。

## 编译环境（重要）

程序**不内置编译器**，用本机的 **MinGW-w64 g++** 编译生成的 C++，参数是 `g++ -std=c++17 -O2 -Wall`。

- 本机开发所用：**MinGW-w64 的 g++ 8.1.0**（w64devkit / MSYS2 的 mingw64 里的 g++ 同一套，随便一个能用就行）。
- 查找顺序（见 [engine.py](engine.py) 的 `_find_gxx()`）：`PATH` → 环境变量 `CXX` / `GXX` → 内置的候选绝对路径 → `C:\`、`D:\`、`E:\`、`Program Files` 等目录浅层扫描。

**换到别人的电脑上，编译器路径基本都不一样，需要二选一改一下：**

| 做法 | 操作 |
| --- | --- |
| 最省事（推荐） | 装 MinGW-w64 或 w64devkit，把它的 `bin` 目录加入系统 `PATH`，程序启动就能自动找到 |
| 不改 PATH | 设环境变量 `CXX=D:\你的路径\bin\g++.exe`，程序会优先用它 |
| 改代码 | 打开 `engine.py`，在 `_find_gxx()` 的 `cands` 列表里加一行你自己电脑上的 `g++.exe` 绝对路径 |

没装或路径不对时，页面右上角会显示「未找到 g++ 编译器」，点了执行也会直接报错，此时不影响提交以外的其他功能。

## 更新记录

### 2026-10 · 样例识别与判定改进

- **样例识别**：从原来的「纯图片提取」改为「以 PDF 文字层为准、样例只作数值参考」。具体做了三件事：
  1. 优先读 PDF 自带的文字层（`pymupdf`），只有扫描版没有文字层时才退回渲染图片；
  2. 抑制「半角数字/字母后紧跟中文」时库自动补出来的虚空格，避免 `6是数字` 被读成 `6 是数字` 而误判样例；
  3. 样例标题兼容 `输入样例1：`、`样例输入3：`、`输入样例`、`输入：` 等多种排版。
- **题目判别**：由「图片识别」改为「文字识别」，题面文字整段喂给模型，不再靠截图看题。
- **样例自检放宽**：不再逐字符苛求空格。只差空格数量或换行位置时判定通过，日志里会标注「其中 N 组只有空格数量不同 / 换行位置不同」；输出格式一律以题目的文字描述（输入说明 / 输出说明）为准。
- **返回判定后的重试提示**：改为提醒模型按文字要求写输出格式，不要照抄样例里可能不规范的空白。

## 实现要点

| 环节 | 做法 |
| --- | --- |
| 登录 / 题库 / 判题 | 全走接口，不用浏览器。登录 `POST /user/login.do`，题目 `GET /contest/problems.do`，结果 `POST /submission/results.do`，都是 JSON |
| 题面 | `GET /problem/downloadTextFile.do?problemId=X` 拿 PDF，PDF 自带文字层，直接抽文本给模型（不截图、不 OCR） |
| 出码 | 智谱 `glm-4.5-flash`，提示词强制「只输出代码 / 标准输入输出 / 必须处理 EOF」 |
| 校验 | `g++ -std=c++17 -Wall` 编译 + 用题面样例实际跑一遍比对 |
| 提交 | `POST /submission/submit.do`，multipart，`sourceFile` 上传 `.cpp`，`languageId=2`（GNU C/C++） |
| 判定 | 提交前记下最大提交号，之后每 3 秒查一次，出现更大的编号且状态非「尚未评测」即为结果 |

## 目录

```
xdoj/
├── 启动.bat           一键启动
├── 使用说明.md         给使用者看的说明
├── server.py          网页服务（FastAPI + SSE）
├── engine.py          刷题引擎（网页和命令行共用）
├── paths.py           路径与配置
├── auto.py            命令行入口
├── desktop.py         桌面壳（Edge --app 窗口，可选）
├── oj/client.py       OJ 接口封装
├── oj/pdftext.py      PDF 转文本 / 样例抽取
├── ai/solver.py       大模型调用与提示词
├── static/index.html  控制台页面
├── app.ico            图标
├── src/               运行后生成 p<题号>.cpp
└── data/shots/        运行后保存题面 p<题号>.pdf / .txt
```

## 注意

- 分发给别人时请删掉 `.venv`（体积大且绑定本机路径）和 `.env`（含自己的账号密钥）；`启动.bat` 会自动重建环境。
- 提交有频率限制，题与题之间默认间隔 5 秒，跑批时不要调太小。
- 编程作业请遵守学校规定，本工具仅用于本地练习与调试。
