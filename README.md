# Shittim Shell Assistant (什亭之匣控制台助手)

老师，这是一个基于《蔚蓝档案》主题开发的 Bash 终端工具。通过此工具 **普拉娜 (Plana)** 与 **阿罗娜 (Arona)** 将进驻您的终端，提供情感陪伴。老师可以在Linux操作系统上尝试运行这个项目。

使用的项目包括：GPT-SoVITS

使用的模型来自：bilibili@SLNeil
（BV1o4fyYuEPW）

核心对话引擎：Ollama (Qwen 2.5:7b, Qwen 2.5:14b)

**模型的主要目的是聊天互动。虽然模型可以实现在终端执行指令的功能，但这不是该模型的主要目的，而且存在较大风险，请谨慎使用。而且现在用的prompt ai真不一定能输出正确格式……**

**这个执行指令用的不是openclaw,而且真的会降低老师的效率，所以……**

**若老师确实想要执行指令，强烈建议使用默认的secure设置，该设置下所有指令都必须在执行前被用户再次确认**

**若老师启用了指令执行功能，请老师确认自己完全理解指令含义。虽然已经尽量多设检测，但是不排除存在问题的可能。若老师使用不当导致包括但不限于文件被删除或系统损坏等问题，开发者不予负责**

**（不要跟我说我写的prompt不符合人设，因为是云玩家（bushi））**

## 📋 依赖要求 (Dependencies)

在运行本项目前，请确保老师的 Linux 环境已安装以下必要组件：

### 1. 核心系统工具
* **Bash (4.0+):** 脚本运行的基础环境
* **bc:** 用于处理复杂的数学运算（如系统负载解析）
* **awk / sed:** 用于提取系统数据及角色状态持久化
* **procps:** 提供 `free` 命令以监控内存占用情况
* **jq:** 用于处理 AI 接口的 JSON 数据。
* **Ollama:** 必须安装。请确保已通过 `ollama pull qwen2.5:7b` `ollama pull qwen2.5:14b`获取对话模型。

### 2. 音频支持
* **pulseaudio-utils:** 必须安装，系统通过 `paplay` 指令驱动语音反馈

**安装参考 (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install bc jq pulseaudio-utils procps coreutils
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
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

老师可以在终端输入 `shittim help` 来查看可用指令
* `time`: 报告当前时间
* `load`: 显示 CPU 与内存负载，并在过载时发出预警
* `ls / find`: 文件检索与目录扫描
* `rain`: 关于下雨天的特别备注
* 老师也可以在终端直接输入 `shittim` ：输出一些预置的文本
* `shittim plana <str>`: 普拉娜会与您互动。
* `free`: 释放 shittim plana <str> 的资源

---

## 更多功能 (Extended Features)

目前已经实现了plana指令自动合成语音的功能，为了调用它，你需要（以下进阶功能配置较难）：
1. 在自己的linux系统上部署 GPT-SoVITS：https://github.com/RVC-Boss/GPT-SoVITS （可能要相应补充一些库）
2. 下载额外的模型
```bash
ollama pull translategemma:4b
ollama pull translategemma:12b
```
3. (config)设置voice=true
4. (shittim_lib)venv设置为自己的虚拟环境，gpt_sovits_path设置为GPT-SoVITS的路径
5. 尝试运行以下代码无误（需要按需更改路径）:
```bash
python api.py -dr "1.wav" -dt "先生の接続プロセスを确认。よろしくお願いします。" -dl "ja" > api.log 2>&1 &

curl -X POST "http://127.0.0.1:9880/set_model"   -H "Content-Type: application/json"   -d '{
    "gpt_model_path": "/home/tzc/my_software/shittim/voice/gpt-sovits/models/Plana-e15.ckpt",
    "sovits_model_path": "/home/tzc/my_software/shittim/voice/gpt-sovits/models/Plana_e16_s208.pth"
  }'

curl -X POST "http://127.0.0.1:9880/"   -H "Content-Type: application/json"   -d '{
    "text": "どの仕事を始めますか、先生。",
    "text_language": "ja"                                                                          
  }' --output ./test/out.wav
```
* 完成以上配置之后，不排除仍然存在一些依赖问题，可能需要自己调整
* 当然，即使老师完成了以上所有这些，最后综合效果也未必一定好：主要原因是语音的情绪过于平淡、输出速度可能过慢

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
1. **silent** 默认设置为false，设置为 true 可全局静音语音反馈
2. **is_exit** 默认设置为false，若设置为 true 将使脚本停止所有响应
3. **characteristic**默认设置为standard,此设置用来选择prompt,有shy,standard,sweet三个选项
4. **next_character** 决定下一次触发时出现的角色（plana 或 arona），不必设置，因为除了plana指令以外两小只都会交替出现
5. **cmd**默认设置为secure（强烈建议）,这样每次执行指令之前都会要求确认。若设置为free,则执行指令无须确认。
6. **cmd_ignore**默认设置为true（建议），即禁用指令执行功能。若想要使用指令执行功能，写入false
7. **memory**默认为recent,也可以设置为recall（plana会回忆与你更加久远的对话）
8. **model**默认为qwen2.5:7b 也可以设置为qwen2.5:14b 也可设置为ollama可以调用的其他模型
9. **voice**默认为false，设置为true开启翻译
10. **translate_model**默认为translategemma:4b 也可设置为ollama可以调用的其他模型
11. **venv**填入虚拟环境的路径，如：venv="/home/xxx/venvs/gpt-sovits"
12. **gpt_sovits_path**填入GPT-SoVITS的路径，如：voice_api="/home/xxx/my_software/GPT-SoVITS"

---