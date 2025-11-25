# 小算算桌宠项目

## python环境配置

```bash
# 新建环境
# 注意避免使用conda，默认使用的是apt在root安装的python
python3 -m venv .venv

# 安装依赖
pip install -r requirements.txt

```
## WSL ubuntu 配置指南

### WSL 调用windows音频配置

1. 在ubuntu中安装PulseAudio
```bash
sudo apt update
sudo apt upgrade
sudo apt install pulseaudio
sudo apt install pulseaudio-utils pavucontrol
```

2. 配置ALSA

在ubuntu中添加该文件

```bash
# ~/.asoundrc

pcm.!default {
    type pulse
    fallback "sysdefault"
    hint {
        show on
        description "Default ALSA Output (via PulseAudio)"
    }
}

ctl.!default {
    type pulse
    fallback "sysdefault"
}

# 显式定义 pulse 设备
pcm.pulse {
    type pulse
}

ctl.pulse {
    type pulse
}
```

3. 执行test/test_audio.py脚本，测试音频设备是否正常
```bash
python3 test/test_audio.py
```


## 脚本使用指南

### echo_node

简单的语音回声系统，将识别的语音直接复述出来。

**功能：** ASR 识别语音 → TTS 复述

**启动：**
```bash
cd demo
./start_echo_system.sh
```

**使用：** 说话后系统会自动复述你说的内容

---

### chat_node

基于 Deepseek 大模型的 AI 对话系统。

**功能：** ASR 识别语音 → Deepseek AI 回答 → TTS 播放回复

**配置 API Key：**
```bash
# 方法1: 环境变量
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 方法2: .env 文件
echo 'DEEPSEEK_API_KEY=sk-your-api-key-here' > .env
```

**启动：**
```bash
cd demo
./start_chat_system.sh
```

**使用：** 说话提问，AI 会智能回答并语音播放

**注意：** 系统会在 AI 思考和语音播放时自动暂停录音，避免回声