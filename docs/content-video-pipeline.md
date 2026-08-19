# Vertical video pipeline

This repository provides the public, parameterized implementation for turning approved visual assets and scene audio into a vertical MP4. Real content packages, source material, account state, and publication records stay in the private operating vault.

## Renderer

The asset-slide renderer is:

```text
engines/motion/render_asset_slide_video.py
```

It accepts a JSON manifest. Paths are resolved relative to that manifest, so the same code works for different content packages without embedding personal absolute paths.

Minimal manifest:

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "label": "AI CONTENT PIPELINE",
  "theme": "frost",
  "out_dir": "out",
  "scenes": [
    {
      "asset": "assets/scene-001.png",
      "audio": "audio/scene-001.mp3",
      "title": "One idea per scene",
      "caption": "Keep the approved visual asset as the main subject."
    }
  ]
}
```

Run:

```bash
python3 engines/motion/render_asset_slide_video.py path/to/manifest.json
```

Requirements:

- Python 3.10+
- Pillow
- `ffmpeg` and `ffprobe`
- a CJK-capable font, supplied by `font` in the manifest, `--font`, or `VIDEO_FONT_PATH`

The renderer creates scene slides, per-scene MP4 files, `manifest.resolved.json`, and `final.mp4` under `out_dir`. It does not upload or publish anything.

## Local validation gate

Check the final file with:

```bash
ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size \
  -of json out/final.mp4
```

The standard contract is 1080×1920, 30fps, H.264 video, AAC audio, no blank frames, and a scene audio/video duration delta below 0.02 seconds.

## Publication evidence gate

Rendering and upload are separate states:

1. local artifact generated;
2. editor/upload state;
3. submission accepted;
4. public publication verified;
5. failed or blocked.

A command callback, editor DOM, `published=true`, `success=true`, or an uploaded blob is not by itself public evidence.

- **Xiaohongshu video:** check the 20-character title limit; enable original declaration for original work; after submission, verify the Creator result or public note listing. A public note URL is stronger than an editor-only callback.
- **X video:** require a public `https://x.com/<user>/status/<id>` URL and verify that the post contains the uploaded video. If no public URL is found, report failed or unverified.

Platform-specific authentication and browser automation remain local adapter concerns and must not be placed in this repository.
