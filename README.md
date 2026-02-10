# ComfyUI Video Concat Sync Node

一个用于 **ComfyUI** 的自定义节点插件：将多个视频片段按顺序拼接，并尽量保证视音频同步。

## 功能

- 支持多段视频输入（每行一个路径，或英文逗号分隔）。
- 先统一每段视频的编码参数（帧率、采样率、声道、时间戳）再拼接，降低音画不同步概率。
- 输出为单一 MP4 文件。

## 节点

- 节点名称：`Video Concat (A/V Sync)`
- 分类：`video`

### 输入参数

- `video_paths`: 视频路径列表（至少 2 段）
- `output_path`: 输出文件路径（默认 `output/concat_sync.mp4`）
- `target_fps`: 统一帧率
- `audio_sample_rate`: 统一音频采样率
- `audio_channels`: 统一音频声道
- `video_crf`: H.264 CRF 质量参数（越小越清晰）
- `preset`: H.264 编码速度预设
- `audio_bitrate_k`: 音频码率（kbps）

## 安装

1. 把本仓库放到 `ComfyUI/custom_nodes/` 下。
2. 确保系统已安装 `ffmpeg`，并可在命令行直接调用。
3. 重启 ComfyUI。

## 注意

- 本节点依赖系统 `ffmpeg`。
- 为保证同步稳定性，节点会先逐段转码，再无损拼接中间文件。
