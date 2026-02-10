import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List


class VideoConcatSyncNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "每行一个视频路径，或使用英文逗号分隔",
                    },
                ),
                "output_path": (
                    "STRING",
                    {
                        "default": "output/concat_sync.mp4",
                    },
                ),
                "target_fps": (
                    "FLOAT",
                    {
                        "default": 30.0,
                        "min": 1.0,
                        "max": 240.0,
                        "step": 0.1,
                    },
                ),
                "audio_sample_rate": (
                    "INT",
                    {
                        "default": 48000,
                        "min": 8000,
                        "max": 192000,
                        "step": 1000,
                    },
                ),
                "audio_channels": (
                    "INT",
                    {
                        "default": 2,
                        "min": 1,
                        "max": 8,
                        "step": 1,
                    },
                ),
                "video_crf": (
                    "INT",
                    {
                        "default": 18,
                        "min": 0,
                        "max": 51,
                        "step": 1,
                    },
                ),
                "preset": (["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"],),
                "audio_bitrate_k": (
                    "INT",
                    {
                        "default": 192,
                        "min": 64,
                        "max": 512,
                        "step": 32,
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "concat_videos"
    CATEGORY = "video"

    @staticmethod
    def _split_paths(raw_paths: str) -> List[str]:
        paths: List[str] = []
        for line in raw_paths.splitlines():
            line = line.strip()
            if not line:
                continue
            for item in line.split(","):
                item = item.strip()
                if item:
                    paths.append(item)
        return paths

    @staticmethod
    def _run(cmd: List[str]) -> None:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{result.stderr}")

    def concat_videos(
        self,
        video_paths: str,
        output_path: str,
        target_fps: float,
        audio_sample_rate: int,
        audio_channels: int,
        video_crf: int,
        preset: str,
        audio_bitrate_k: int,
    ):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("未找到 ffmpeg。请先在系统中安装 ffmpeg 并确保其在 PATH 中。")

        input_files = self._split_paths(video_paths)
        if len(input_files) < 2:
            raise ValueError("至少需要 2 个视频片段进行拼接。")

        resolved_inputs = []
        for path in input_files:
            p = Path(path).expanduser().resolve()
            if not p.exists() or not p.is_file():
                raise FileNotFoundError(f"输入视频不存在: {p}")
            resolved_inputs.append(p)

        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="comfyui_concat_") as temp_dir:
            temp_root = Path(temp_dir)
            normalized_files = []

            for idx, src in enumerate(resolved_inputs):
                normalized = temp_root / f"norm_{idx:04d}.mp4"
                cmd = [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(src),
                    "-vf",
                    f"fps={target_fps},format=yuv420p",
                    "-af",
                    "aresample=async=1:first_pts=0,asetpts=PTS-STARTPTS",
                    "-r",
                    str(target_fps),
                    "-ar",
                    str(audio_sample_rate),
                    "-ac",
                    str(audio_channels),
                    "-c:v",
                    "libx264",
                    "-preset",
                    preset,
                    "-crf",
                    str(video_crf),
                    "-c:a",
                    "aac",
                    "-b:a",
                    f"{audio_bitrate_k}k",
                    "-movflags",
                    "+faststart",
                    str(normalized),
                ]
                self._run(cmd)
                normalized_files.append(normalized)

            concat_file = temp_root / "concat_list.txt"
            with concat_file.open("w", encoding="utf-8") as f:
                for p in normalized_files:
                    safe_path = str(p).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            concat_cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output),
            ]
            self._run(concat_cmd)

        return (str(output),)


NODE_CLASS_MAPPINGS = {
    "VideoConcatSync": VideoConcatSyncNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoConcatSync": "Video Concat (A/V Sync)",
}
