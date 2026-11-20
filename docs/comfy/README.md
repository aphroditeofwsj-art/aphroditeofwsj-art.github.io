# ComfyUI 怪物精灵工作流

用本地 **ComfyUI + SDXL Turbo** 复现《海拉鲁失落王国》里 4 类怪物的像素精灵，
工作流本身可以直接拖进 ComfyUI 打开、改提示词、换种子后复跑。

![工作流与产出](workflow-preview.png)

## 文件

| 文件 | 用途 |
| --- | --- |
| `monster-sprites.workflow.json` | **ComfyUI 界面工作流**：在 ComfyUI 里拖入 / `工作流 → 打开` 即可加载 |
| `monster-sprites.api.json` | `/prompt` 接口格式，用于脚本批量出图 |
| `generate.py` | 批量出图脚本（改提示词、种子后直接跑） |
| `samples/*.png` | 本次实际生成的 4 张怪物精灵（512×512） |
| `workflow-preview.png` | 工作流界面截图 + 4 张产出的组合图 |

## 环境

- ComfyUI `0.39.2`（本地源码部署，`--listen 127.0.0.1 --port 8188`）
- 模型：`sd_xl_turbo_1.0_fp16.safetensors`（SDXL Turbo，无 LoRA / 无 ControlNet）
- 显卡：RTX 5050 Laptop（8 GB VRAM），单张耗时 **5–10 秒**
- 采样：`euler_ancestral` + `normal`，**6 steps**，**CFG 1.5**，1024×1024 出图

## 工作流结构

```
CheckpointLoaderSimple → CLIPTextEncode(正) ┐
                       → CLIPTextEncode(负) ├→ KSampler → VAEDecode
                       → EmptyLatentImage   ┘                 │
                                                              ▼
                              SaveImage ← ImageScale(512) ← ImageScale(64)
```

| 节点 | 作用 | 关键参数 |
| --- | --- | --- |
| `CheckpointLoaderSimple` | 载入 SDXL Turbo | `sd_xl_turbo_1.0_fp16.safetensors` |
| `CLIPTextEncode` ×2 | 正向 / 负向提示词 | 见下表；负向统一排除写实风、文字、水印 |
| `EmptyLatentImage` | 出图尺寸 | 1024 × 1024，batch 1 |
| `KSampler` | 采样 | seed 可控，6 steps，CFG 1.5，euler_ancestral / normal |
| `VAEDecode` | 解码成图像 | — |
| `ImageScale` #1 | **像素化降采样** | `nearest-exact`，1024 → **64×64** |
| `ImageScale` #2 | **像素化放大** | `nearest-exact`，64 → **512×512** |
| `SaveImage` | 落盘 | 前缀 `monster_sprite` |

**为什么先降后升**：SDXL 直接生成的图边缘是平滑渐变的，和游戏 16-bit 像素风不搭。
先用最近邻插值压到 64×64 丢掉细节，再用最近邻放大回 512，就得到边缘硬、色块干净的像素画，
放大过程不会引入模糊——这是把 AI 插画转成游戏可用像素素材的关键一步。

## 4 只怪物的提示词与结果

统一风格后缀：`16-bit pixel art, SNES retro game sprite, limited palette, bold black outline, flat shading, centered single character on plain dark background, game asset`

| 怪物 | seed | 提示词主体 | 产出 |
| --- | --- | --- | --- |
| 乌贼 squid | 7101 | cute but menacing squid monster with long tentacles, cyan and teal body, glowing yellow eyes, floating over swamp | `samples/squid.png` |
| 浣熊 raccoon | 7102 | fierce giant raccoon beast with sharp claws, grey and black striped fur, glowing red eyes, crouching in dark mossy forest | `samples/raccoon.png` |
| 幽灵 spirit | 7103 | ghostly spirit wisp monster, translucent pale blue body, crackling white lightning around it, glowing empty eyes | `samples/spirit.png` |
| 竹妖 bamboo | 7104 | plant monster made of green bamboo stalks, sharp leaf blades, wooden bark face, sinister grin | `samples/bamboo.png` |

## 怎么用

**在 ComfyUI 里**：把 `monster-sprites.workflow.json` 直接拖进 ComfyUI 画布（或 `工作流 → 打开`），
改 `CLIPTextEncode` 里的提示词、改 `KSampler` 的 seed，点「运行」即可。工作流里带一个 Note 节点记录参数。

**用脚本批量跑**（需要服务在 8188 端口）：

```bash
python docs/comfy/generate.py
```

脚本会把 4 只怪物依次跑一遍并保存到 `docs/comfy/samples/`。

## 调参经验

- **步数**：Turbo 模型 4–8 步足够，超过 10 步反而可能出现噪点；6 步是画质/速度的平衡点
- **CFG**：Turbo 建议 1.0–2.0，给太高（>3）会过曝、色块崩
- **种子**：同一提示词换种子，怪物姿势/配色变化很大，批量出 4–8 张再挑是常规做法
- **像素化尺寸**：`64×64` 适合游戏内 32–64px 的精灵；想要更粗的颗粒可以降到 48 或 32
