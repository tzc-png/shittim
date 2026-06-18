# Shittim Shell Assistant (什亭之匣控制台助手)

老师，这是一个基于《蔚蓝档案》主题开发的 Bash 终端工具。通过此工具 **普拉娜 (Plana)** 与 **阿罗娜 (Arona)** 将进驻您的终端，提供情感陪伴。老师可以在Linux操作系统上尝试运行这个项目。

主要使用的项目：GPT-SoVITS

使用的模型来自：bilibili@SLNeil
（BV1o4fyYuEPW）

核心对话引擎：Ollama (Qwen 2.5:7b, Qwen 2.5:14b) / 自备API


## 🚀 快速安装 (Quick Start)

### 1. 部署项目
建议老师将项目文件夹放置于您的家目录下(也可以放在其他路径)：
```bash
git clone <your-repo-url> ~/shittim
cd ~/shittim
```

### 2. Linux 基础环境
以下组件通常已随系统预装：
-sed
-awk
-bash
-coreutils
-procps

安装项目所需额外依赖：
```bash
sudo apt update

sudo apt install bc jq curl pulseaudio-utils
```

部署本地模型（可以用api替代，若要替代，配置ENABLE_CHAT_API为true）
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

### 3. 执行配置脚本并激活更改
```bash
sh ./setup.sh
```

执行以下命令或重新打开终端：
```bash
source ~/.bashrc
```

### 4. 图形化config配置
```bash
pip install kconfiglib
```

### 5. 语音输出配置
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
* `Plana-e15.ckpt`以及`Plana_e16_s208.pth`放到`/shittim/voice/GPT-Sovits/models`
* `pytorch_model.bin`放到`/shittim/voice/GPT-Sovits/plana_engine/pretrained_models/chinese-hubert-base`
* 链接:https://pan.baidu.com/s/1uW2DfQESnsDdDdXeMpMq3A?pwd=72e8 

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
4. **memory**设置“回忆”的对话数
5. **model**默认为qwen2.5:7b  也可设置为ollama可以调用的其他模型(如qwen2.5:14b)
6. **voice**默认为false，设置为true开启翻译
7. **translate_model**默认为translategemma:4b 也可设置为ollama可以调用的其他模型
8. **venv**虚拟环境路径，需要指定，如：/home/tzc/miniconda3/envs/plana
9. **API_KEY** **BASE_URL** **MODEL_NAME** 为api配置，若不使用可留空
10. **ENABLE_CHAT_API** **ENABLE_TRANS_API**设置对话以及翻译是否用api (true or false)

---