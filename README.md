# Shittim Shell Assistant (什亭之匣控制台助手)

老师，这是一个基于《蔚蓝档案》主题开发的 Bash 终端工具。通过此工具 **普拉娜 (Plana)** 与 **阿罗娜 (Arona)** 将进驻您的终端，提供情感陪伴。老师可以在Linux操作系统上尝试运行这个项目。

使用的项目包括：GPT-SoVITS

使用的模型来自：bilibili@SLNeil
（BV1o4fyYuEPW）

核心对话引擎：Ollama (Qwen 2.5:7b, Qwen 2.5:14b)

**暂时去除所有指令执行相关功能**
**（不要跟我说我写的prompt不符合人设，因为是云玩家（bushi））**

## 📋 依赖要求 (Dependencies)

在运行本项目前，请确保老师的 Linux 环境已安装以下必要组件：

### 1. 核心系统工具
* **Bash (4.0+):** 脚本运行的基础环境
* **bc:** 用于处理复杂的数学运算（如系统负载解析）
* **awk / sed:** 用于提取系统数据及角色状态持久化
* **procps:** 提供 `free` 命令以监控内存占用情况
* **jq:** 用于处理 AI 接口的 JSON 数据。
* **Ollama:** 请确保已通过 `ollama pull qwen2.5:7b` 获取对话模型，若决定完全使用api,可以配置config中的ENABLE_CHAT_API以及ENABLE_TRANS_API都为true。

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
建议老师将项目文件夹放置于您的家目录下(也可以是的其他路径)：
```bash
git clone <your-repo-url> ~/shittim
cd ~/shittim
```

### 2. 执行配置协议
按照“依赖要求”进行工具安装。

在此基础上我们提供了一键配置脚本，会自动处理终端配色（PS1）、路径设置（PATH）以及开机唤醒逻辑：
```bash
sh ./setup.sh
```

### 3. 激活更改
执行以下命令或重新打开终端，即可完成什亭之匣的连接：
```bash
source ~/.bashrc
```

### 4. 语音输出
执行以下命令来下载必要组建配置虚拟环境：
```bash
conda create -n plana python=3.10
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install numpy soundfile librosa transformers einops omegaconf librosa phonemizer pytorch-lightning matplotlib pyopenjtalk
```

测试方式：
```bash
conda activate plana
python plana_tts_server.py &
```

```bash
echo '{"text":"テストです。","out":"/tmp/test.wav"}' | nc -U /tmp/plana_tts.sock
aplay /tmp/test.wav
```

按需下载翻译模型（可以用api替代，若要替代，配置ENABLE_TRANS_API为true）
```bash
ollama pull translategemma:4b
```

还需要下载模型文件，我放在了网盘上，下载解压后：

Plana-e15.ckpt以及Plana_e16_s208.pth放到/shittim/voice/GPT-Sovits/models

pytorch_model.bin放到/shittim/voice/GPT-Sovits/plana_engine/pretrained_models/chinese-hubert-base

【超级会员V4】通过百度网盘分享的文件：upload
链接:https://pan.baidu.com/s/1uW2DfQESnsDdDdXeMpMq3A?pwd=72e8 
复制这段内容打开「百度网盘APP 即可获取」
---

## 🛠️ 功能列表 (Features)

老师可以在终端输入 `shittim help` 来查看可用指令
* `time`: 报告当前时间
* `load`: 显示 CPU 与内存负载，并在过载时发出预警
* `ls / find`: 文件检索与目录扫描
* `rain`: 关于下雨天的特别备注
* 老师也可以在终端直接输入 `shittim` ：输出一些预置的文本
* `shittim plana <str>`: 普拉娜会与您互动。
* `startup`: 提前准备普拉娜的对话（申请显存、运行脚本）
* `free`: 释放 shittim plana <str> 的资源
* `resetproxy`: 关闭代理

---

## ⚠️ 注意事项 (Notes)

1. **路径自适应:** 脚本会自动识别自身所在位置。请确保 `shittim_lib` 与主脚本处于同一目录下
2. **角色切换逻辑:** 普拉娜与阿罗娜会通过 `config` 文件记录状态。请勿手动删除此文件，否则切换协议将会失效
3. **VSCode 环境:** 如果老师在 VSCode 内部终端使用，语音播放默认处于静音状态，以防干扰老师的工作。
4. **音频文件:** 所有的语音资源已按角色分类存放于 `voice/` 目录下

---

## ⚙️ 设置 (Settings)

设置的内容存在4个地方确认：config,README.md,setup,shittim_lib
老师可以通过编辑config进行设置
1. **silent** 默认设置为false，设置为 true 可全局静音语音反馈，也可以设置为system根据当前是否为power-saver自动判断
2. **is_exit** 默认设置为false，若设置为 true 将使脚本停止所有响应
3. **next_character** 决定下一次触发时出现的角色（plana 或 arona），不必设置，因为除了plana指令以外两小只都会交替出现
4. **cmd**默认设置为secure（强烈建议）,这样每次执行指令之前都会要求确认。若设置为free,则执行指令无须确认。
5. **cmd_ignore**默认设置为true（建议），即禁用指令执行功能。若想要使用指令执行功能，写入false
6. **memory**设置“回忆”的对话数
7. **model**默认为qwen2.5:7b  也可设置为ollama可以调用的其他模型(如qwen2.5:14b)
8. **voice**默认为false，设置为true开启翻译
9. **translate_model**默认为translategemma:4b 也可设置为ollama可以调用的其他模型
10. **venv**虚拟环境路径，需要指定，如：/home/tzc/miniconda3/envs/plana
11. **API_KEY** **BASE_URL** **MODEL_NAME** 为api配置，若不使用可留空
12. **ENABLE_CHAT_API** **ENABLE_TRANS_API**设置对话以及翻译是否用api (true or false)

---