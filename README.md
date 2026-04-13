# Shittim Shell Assistant (什亭之匣控制台助手)

这是一个基于《蔚蓝档案》主题开发的 Bash 终端工具。通过此工具 **普拉娜 (Plana)** 与 **阿罗娜 (Arona)** 将进驻您的终端，提供情感陪伴。

使用的项目包括：GPT-SoVITS

使用的模型来自：bilibili@SLNeil
（BV1o4fyYuEPW）

核心对话引擎：Ollama (Qwen 2.5:7b)

**模型的主要目的是聊天互动。虽然模型可以实现在终端执行指令的功能，但这不是该模型的主要目的，而且存在较大风险，请谨慎使用**

**若确实想要执行指令，强烈建议使用默认的secure设置，该设置下所有指令都必须在执行前被用户再次确认**

**如开发者**

## 📋 依赖要求 (Dependencies)

在运行本项目前，请确保您的 Linux 环境已安装以下必要组件：

### 1. 核心系统工具
* **Bash (4.0+):** 脚本运行的基础环境
* **bc:** 用于处理复杂的数学运算（如系统负载解析）
* **awk / sed:** 用于提取系统数据及角色状态持久化
* **procps:** 提供 `free` 命令以监控内存占用情况
* **jq:** 用于处理 AI 接口的 JSON 数据。
* **Ollama:** 必须安装。请确保已通过 `ollama pull qwen2.5:7b` 获取对话模型。

### 2. 音频支持
* **pulseaudio-utils:** 必须安装，系统通过 `paplay` 指令驱动语音反馈

**安装参考 (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install bc jq pulseaudio-utils procps coreutils
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

---

## 🚀 快速安装 (Quick Start)

### 1. 部署项目
建议将项目文件夹放置于您的家目录下(也可以是的其他路径)：
```bash
git clone <your-repo-url> ~/shittim
cd ~/shittim
```

### 2. 执行配置协议
我们提供了一键配置脚本，会自动处理终端配色（PS1）、路径设置（PATH）以及开机唤醒逻辑：
```bash
sh ./setup.sh
```

### 3. 激活更改
执行以下命令或重新打开终端，即可完成什亭之匣的连接：
```bash
source ~/.bashrc
```

---

## 🛠️ 功能列表 (Features)

您可以在终端输入 `shittim help` 来查看可用指令
* `time`: 报告当前时间
* `load`: 显示 CPU 与内存负载，并在过载时发出预警
* `ls / find`: 文件检索与目录扫描
* `rain`: 关于下雨天的特别备注
* 也可以在终端直接输入 `shittim` ：输出一些预置的文本
* `shittim plana <str>`: 普拉娜会以文静、理性的性格与您互动。

---

## ⚠️ 注意事项 (Notes)

1. **路径自适应:** 脚本会自动识别自身所在位置。请确保 `shittim_lib` 与主脚本处于同一目录下
2. **角色切换逻辑:** 普拉娜与阿罗娜会通过 `config` 文件记录状态。请勿手动删除此文件，否则切换协议将会失效
3. **VSCode 环境:** 如果您在 VSCode 内部终端使用，语音播放默认处于静音状态，以防干扰您的工作。
4. **音频文件:** 所有的语音资源已按角色分类存放于 `voice/` 目录下

---

## ⚙️ 设置 (Settings)

您可以通过编辑config进行设置
1. **next_character** 决定下一次触发时出现的角色（"plana" 或 "arona"）
2. **silent** 设置为 true 可全局静音语音反馈
3. **vscode_play** 设置为 true 后，即使在 VSCode 终端内也会播放语音
4. **exit** 设置为 true 将使脚本停止所有响应
5. **characteristic**设置prompt,有shy,shy_simple,enthusiastic三个选项
6. **cmd**默认设置为secure,这样每次执行指令之前都会要求确认。若设置为free,则执行指令无须确认。强烈建议使用secure
7. **cmd_ignore**默认设置为true，即禁用指令执行功能。一般建议使用true。若需要使用指令执行功能，写入false
