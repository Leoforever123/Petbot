# 小算算桌宠项目

## WSL ubuntu 配置指南

```
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