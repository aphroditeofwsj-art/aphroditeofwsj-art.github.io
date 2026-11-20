"""生成《海拉鲁失落王国》怪物精灵的 ComfyUI 工作流 + 实际出图。

产出：
  monster-sprites.workflow.json  —— ComfyUI 界面可直接拖入/打开的工作流（用于展示）
  monster-sprites.api.json       —— /prompt 接口用的 API 格式（用于脚本批量跑）
  samples/*.png                  —— 4 只怪物的生成结果
"""
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = "http://127.0.0.1:8188"
OUT_DIR = Path(r"E:\comfyio\out\monsters")
DOC_DIR = Path(r"E:\deepseek harmess\game-fix\repo\docs\comfy")
SAMPLE_DIR = DOC_DIR / "samples"
for d in (OUT_DIR, DOC_DIR, SAMPLE_DIR):
    d.mkdir(parents=True, exist_ok=True)

CKPT = "sd_xl_turbo_1.0_fp16.safetensors"
NEG = "blurry, low quality, watermark, text, signature, photo, 3d render, realistic, extra limbs, deformed, blurry edges"
STYLE = "16-bit pixel art, SNES retro game sprite, limited palette, bold black outline, flat shading, centered single character on plain dark background, game asset"

NOTE_TEXT = """海拉鲁失落王国 · 怪物精灵生成工作流

1) SDXL Turbo 文生图（6 steps / CFG 1.5 / euler_ancestral）
2) 最近邻降到 64x64，再最近邻放大到 512x512 —— 得到硬边像素块
3) 保存到 samples/

换怪物只需改「正向提示词」和 KSampler 的 seed；
批量出图用同目录下的 monster-sprites.api.json。"""

# ---------------------------------------------------------------- UI 工作流
def ui_workflow(prompt, seed):
    nodes = [
        {"id": 1, "type": "CheckpointLoaderSimple", "pos": [40, 320], "size": [340, 100],
         "flags": {}, "order": 0, "mode": 0, "inputs": [],
         "outputs": [{"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                     {"name": "CLIP", "type": "CLIP", "links": [2, 3], "slot_index": 1},
                     {"name": "VAE", "type": "VAE", "links": [4], "slot_index": 2}],
         "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
         "widgets_values": [CKPT]},

        {"id": 2, "type": "CLIPTextEncode", "pos": [420, 100], "size": [420, 180],
         "flags": {}, "order": 1, "mode": 0,
         "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
         "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5], "slot_index": 0}],
         "properties": {"Node name for S&R": "CLIPTextEncode"},
         "widgets_values": [prompt]},

        {"id": 3, "type": "CLIPTextEncode", "pos": [420, 330], "size": [420, 140],
         "flags": {}, "order": 2, "mode": 0,
         "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
         "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "slot_index": 0}],
         "properties": {"Node name for S&R": "CLIPTextEncode"},
         "widgets_values": [NEG]},

        {"id": 4, "type": "EmptyLatentImage", "pos": [420, 520], "size": [340, 110],
         "flags": {}, "order": 3, "mode": 0, "inputs": [],
         "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
         "properties": {"Node name for S&R": "EmptyLatentImage"},
         "widgets_values": [1024, 1024, 1]},

        {"id": 5, "type": "KSampler", "pos": [880, 240], "size": [340, 260],
         "flags": {}, "order": 4, "mode": 0,
         "inputs": [{"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 5},
                    {"name": "negative", "type": "CONDITIONING", "link": 6},
                    {"name": "latent_image", "type": "LATENT", "link": 7}],
         "outputs": [{"name": "LATENT", "type": "LATENT", "links": [8], "slot_index": 0}],
         "properties": {"Node name for S&R": "KSampler"},
         "widgets_values": [seed, "randomize", 6, 1.5, "euler_ancestral", "normal", 1.0]},

        {"id": 6, "type": "VAEDecode", "pos": [1260, 240], "size": [210, 60],
         "flags": {}, "order": 5, "mode": 0,
         "inputs": [{"name": "samples", "type": "LATENT", "link": 8},
                    {"name": "vae", "type": "VAE", "link": 4}],
         "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [9], "slot_index": 0}],
         "properties": {"Node name for S&R": "VAEDecode"}, "widgets_values": []},

        {"id": 7, "type": "ImageScale", "pos": [1510, 240], "size": [320, 130],
         "flags": {}, "order": 6, "mode": 0,
         "inputs": [{"name": "image", "type": "IMAGE", "link": 9}],
         "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10], "slot_index": 0}],
         "properties": {"Node name for S&R": "ImageScale"},
         "widgets_values": ["nearest-exact", 64, 64, "disabled"]},

        {"id": 8, "type": "ImageScale", "pos": [1510, 420], "size": [320, 130],
         "flags": {}, "order": 7, "mode": 0,
         "inputs": [{"name": "image", "type": "IMAGE", "link": 10}],
         "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [11, 12], "slot_index": 0}],
         "properties": {"Node name for S&R": "ImageScale"},
         "widgets_values": ["nearest-exact", 512, 512, "disabled"]},

        {"id": 9, "type": "SaveImage", "pos": [1870, 200], "size": [520, 460],
         "flags": {}, "order": 8, "mode": 0,
         "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
         "outputs": [],
         "properties": {}, "widgets_values": ["monster_sprite"]},

        {"id": 10, "type": "PreviewImage", "pos": [1870, 700], "size": [380, 400],
         "flags": {}, "order": 9, "mode": 0,
         "inputs": [{"name": "images", "type": "IMAGE", "link": 12}],
         "outputs": [],
         "properties": {}, "widgets_values": []},

        {"id": 11, "type": "Note", "pos": [40, 40], "size": [740, 230],
         "flags": {}, "order": 10, "mode": 0, "inputs": [], "outputs": [],
         "properties": {}, "widgets_values": [NOTE_TEXT]},
    ]

    links = [
        [1, 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 2, 0, "CLIP"],
        [3, 1, 1, 3, 0, "CLIP"],
        [4, 1, 2, 6, 1, "VAE"],
        [5, 2, 0, 5, 1, "CONDITIONING"],
        [6, 3, 0, 5, 2, "CONDITIONING"],
        [7, 4, 0, 5, 3, "LATENT"],
        [8, 5, 0, 6, 0, "LATENT"],
        [9, 6, 0, 7, 0, "IMAGE"],
        [10, 7, 0, 8, 0, "IMAGE"],
        [11, 8, 0, 9, 0, "IMAGE"],
        [12, 8, 0, 10, 0, "IMAGE"],
    ]

    groups = [
        {"title": "① SDXL Turbo 文生图（6 steps / CFG 1.5）", "bounding": [350, 20, 1130, 640],
         "color": "#3f789e", "font_size": 26, "flags": {}},
        {"title": "② 像素化后处理（最近邻 64 → 512）", "bounding": [1450, 160, 420, 420],
         "color": "#8A8", "font_size": 26, "flags": {}},
        {"title": "③ 输出", "bounding": [1830, 130, 600, 1030],
         "color": "#b58b2a", "font_size": 26, "flags": {}},
    ]

    return {
        "last_node_id": 11,
        "last_link_id": 12,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {"ds": {"scale": 0.62, "offset": [20, 80]}},
        "version": 0.4,
    }


# ---------------------------------------------------------------- API 工作流
def api_workflow(prompt, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 6, "cfg": 1.5, "sampler_name": "euler_ancestral",
            "scheduler": "normal", "denoise": 1.0,
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "ImageScale", "inputs": {"image": ["6", 0], "upscale_method": "nearest-exact",
                                                     "width": 64, "height": 64, "crop": "disabled"}},
        "8": {"class_type": "ImageScale", "inputs": {"image": ["7", 0], "upscale_method": "nearest-exact",
                                                     "width": 512, "height": 512, "crop": "disabled"}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "monster_sprite", "images": ["8", 0]}},
    }


# ---------------------------------------------------------------- 出图
MONSTERS = [
    {
        "key": "squid",
        "name": "乌贼",
        "seed": 7101,
        "prompt": ("cute but menacing squid monster with long tentacles, cyan and teal body, "
                   "glowing yellow eyes, floating over swamp, " + STYLE),
    },
    {
        "key": "raccoon",
        "name": "浣熊",
        "seed": 7102,
        "prompt": ("fierce giant raccoon beast with sharp claws, grey and black striped fur, "
                   "glowing red eyes, crouching in dark mossy forest, " + STYLE),
    },
    {
        "key": "spirit",
        "name": "幽灵",
        "seed": 7103,
        "prompt": ("ghostly spirit wisp monster, translucent pale blue body, crackling white lightning "
                   "around it, glowing empty eyes, " + STYLE),
    },
    {
        "key": "bamboo",
        "name": "竹妖",
        "seed": 7104,
        "prompt": ("plant monster made of green bamboo stalks, sharp leaf blades, wooden bark face, "
                   "sinister grin, " + STYLE),
    },
]


def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=120) as r:
        return json.loads(r.read().decode())


def run(prompt, seed, out_path):
    resp = post("/prompt", {"prompt": api_workflow(prompt, seed), "client_id": str(uuid.uuid4())})
    pid = resp["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 300:
        h = get(f"/history/{pid}")
        if pid in h:
            imgs = []
            for node in h[pid].get("outputs", {}).values():
                imgs += node.get("images", [])
            if imgs:
                q = urllib.parse.urlencode({"filename": imgs[0]["filename"],
                                            "subfolder": imgs[0].get("subfolder", ""),
                                            "type": imgs[0].get("type", "output")})
                with urllib.request.urlopen(f"{BASE}/view?{q}", timeout=60) as r:
                    out_path.write_bytes(r.read())
                return time.time() - t0
        time.sleep(1)
    raise SystemExit("timeout waiting for image")


def main():
    for m in MONSTERS:
        wf_path = DOC_DIR / "tmp.workflow.json"
        wf_path.write_text(json.dumps(ui_workflow(m["prompt"], m["seed"]), ensure_ascii=False, indent=2),
                           encoding="utf-8")
        took = run(m["prompt"], m["seed"], SAMPLE_DIR / f"{m['key']}.png")
        print(f"  {m['name']:4} ({m['key']:8}) seed={m['seed']}  {took:.1f}s")

    # 主工作流文件：用第一只怪物的提示词作为示例
    first = MONSTERS[0]
    (DOC_DIR / "monster-sprites.workflow.json").write_text(
        json.dumps(ui_workflow(first["prompt"], first["seed"]), ensure_ascii=False, indent=2), encoding="utf-8")
    (DOC_DIR / "monster-sprites.api.json").write_text(
        json.dumps(api_workflow(first["prompt"], first["seed"]), ensure_ascii=False, indent=2), encoding="utf-8")
    (DOC_DIR / "tmp.workflow.json").unlink(missing_ok=True)

    print("\nworkflow + samples written to", DOC_DIR)


if __name__ == "__main__":
    main()
