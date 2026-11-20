# AI 生成素材说明（ComfyUI / SDXL Turbo）

游戏剧情演出用到的 5 张插画全部在本地用 ComfyUI 生成，流程可复现。

## 环境

- ComfyUI 0.39.2（本地源码部署，`--listen 127.0.0.1 --port 8188`）
- 模型：`sd_xl_turbo_1.0_fp16.safetensors`（SDXL Turbo，无 LoRA）
- 硬件：NVIDIA RTX 5050 Laptop GPU（8 GB VRAM），单张约 3–13 秒
- 采样：`euler_ancestral` + `normal`，**6 steps**，**CFG 1.5**，分辨率 **1152×448**

## 出图 → 入包 的处理链

1. SDXL Turbo 输出 1152×448 的插画；
2. 按 960:360（8:3）居中裁剪，去掉多余的天/地；
3. 最近邻缩到 480×180，再最近邻放大到 960×360 —— 这一步把平滑插画压成块状像素，和游戏内 16-bit 观感统一；
4. 保存为 `assets/sceneN.png`，由 `intro.py` 在剧情第 4 / 7 / 8 / 18 / 20 页加载显示。

对应的 Python 客户端脚本见仓库外的 `gen.py`（调用 ComfyUI `/prompt` + `/history` + `/view` 接口）。

## 5 张图的提示词与种子

统一风格后缀（`$common`）：
`16-bit pixel art, SNES-style retro game illustration, limited palette, crisp pixel edges, cinematic wide composition`

统一负向词：
`text, watermark, signature, blurry, low quality, photorealistic, 3d render, extra limbs, deformed`

| 文件 | seed | 正向提示词（`$common` 已省略） |
| --- | --- | --- |
| `scene1.png` | 4201 | young hero waking up in a misty grassy field at dawn, holding a rusty ancient sword, distant fantasy kingdom silhouette, `$common` |
| `scene2.png` | 4202 | dark armored demon king with glowing red eyes leading an army of monsters toward a white stone castle, stormy purple sky, lightning, smoke and fire, dark fantasy, `$common` |
| `scene3.png` | 4203 | fierce giant raccoon beast with sharp claws in a dark mossy forest, glowing eyes, moonlit, dark fantasy, `$common` |
| `scene4.png` | 4204 | fast squid-like monster with tentacles hovering over a swamp pond, glowing cyan eyes, murky water, dark fantasy, `$common` |
| `scene5.png` | 4205 | adventurer standing on a cliff overlooking a vast green fantasy landscape with waterfalls, mountains and distant castle ruins, treasure chest nearby, `$common` |

## 说明

- 生成过程完全离线：模型、推理、后处理都在本机完成，没有调用在线生图 API。
- 游戏其余精灵、瓦片、音效不是 AI 生成的，来自原有的像素素材包。
