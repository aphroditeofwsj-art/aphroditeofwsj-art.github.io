"""按 denoise 0.45 复刻 4 只怪物，输出对比图 + 仓库素材。"""
import glob
import io
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from PIL import Image, ImageFilter

BASE = "http://127.0.0.1:8188"
IN_DIR = Path(r"E:\comfyio\in")
OUT = Path(r"E:\comfyio\out\repro")
REPO = Path(r"E:\deepseek harmess\game-fix\repo\docs\comfy")
SAMPLES = REPO / "samples"
REFS = REPO / "references"
for d in (IN_DIR, OUT, SAMPLES, REFS):
    d.mkdir(parents=True, exist_ok=True)

GAME = Path(r"D:\unity program\king-game\web\graphics\monsters")
CKPT = "sd_xl_turbo_1.0_fp16.safetensors"
DENOISE = 0.45

MONSTERS = {
    "squid": ("orange and coral squid monster with spiky tentacles pointing outward, two black dot eyes, "
              "dark red mouth band, thin orange legs, 16-bit pixel art, thick black outline, flat colors, "
              "plain black background"),
    "raccoon": ("tan and brown raccoon beast, cream fur on top of head, angry face with fangs, dark red eyes, "
                "pink belly, big paws with claws, 16-bit pixel art, thick black outline, flat colors, "
                "plain black background"),
    "spirit": ("pale blue and white ghost blob monster, light blue outline, two black oval eyes, rounded body, "
               "16-bit pixel art, thick black outline, flat colors, plain black background"),
    "bamboo": ("green bamboo plant monster, lighter green face area, dark green outline, tendril legs, "
               "16-bit pixel art, thick black outline, flat colors, plain black background"),
}
NEG = ("blurry, low quality, text, watermark, photo, 3d render, realistic, scenery, background objects, "
       "extra limbs, different colors")
SEEDS = {"squid": 5150, "raccoon": 5151, "spirit": 5152, "bamboo": 5153}


def idle_frame(monster):
    files = [p for p in glob.glob(str(GAME / monster / "idle" / "*.png")) if Path(p).stem.isdigit()]
    files.sort(key=lambda p: int(Path(p).stem))
    return files[0]


def prep(monster):
    im = Image.open(idle_frame(monster)).convert("RGBA")
    alpha = im.getchannel("A")
    flat = Image.new("RGB", im.size, (0, 0, 0))
    flat.paste(im, mask=alpha)
    up = flat.resize((512, 512), Image.NEAREST)
    name = f"repro_{monster}.png"
    up.save(IN_DIR / name)
    up.save(REFS / f"{monster}_reference.png")      # 同时留一份到仓库
    return name, alpha, im.size, up


def api(prompt, image_name, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "5": {"class_type": "ImageScale", "inputs": {"image": ["4", 0], "upscale_method": "nearest-exact",
                                                     "width": 512, "height": 512, "crop": "disabled"}},
        "6": {"class_type": "VAEEncode", "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 10, "cfg": 1.8, "sampler_name": "euler_ancestral",
            "scheduler": "normal", "denoise": DENOISE,
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "monster_repro", "images": ["8", 0]}},
    }


def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=120) as r:
        return json.loads(r.read().decode())


def run(wf):
    pid = post("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
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
                    return r.read(), time.time() - t0
        time.sleep(1)
    raise SystemExit("timeout")


def main():
    rows = []
    for monster, prompt in MONSTERS.items():
        name, alpha, size, _ = prep(monster)
        data, took = run(api(prompt, name, SEEDS[monster]))
        res = Image.open(io.BytesIO(data)).convert("RGB")
        m = alpha.resize(res.size, Image.NEAREST).filter(ImageFilter.MaxFilter(3))
        rgba = res.convert("RGBA")
        rgba.putalpha(m)
        (OUT / f"{monster}_raw.png").write_bytes(data)
        rgba.save(SAMPLES / f"{monster}.png")          # 仓库里的成品（512）
        small = rgba.resize(size, Image.LANCZOS)       # 游戏内尺寸
        small.save(OUT / f"{monster}_{size[0]}.png")

        src = Image.open(idle_frame(monster)).convert("RGBA")
        rows.append((monster, src, rgba))
        print(f"{monster:8} {took:5.1f}s  repro={rgba.size} game={size}")

    # 对比图：上排原图、下排 AI 复刻
    cell = 300
    sheet = Image.new("RGB", (cell * 4, cell * 2 + 8), (18, 20, 26))
    for i, (monster, src, rgba) in enumerate(rows):
        b1 = Image.new("RGB", src.size, (32, 44, 32))
        b1.paste(src, mask=src.getchannel("A"))
        sheet.paste(b1.resize((cell, cell), Image.NEAREST), (i * cell, 0))
        b2 = Image.new("RGB", rgba.size, (32, 44, 32))
        b2.paste(rgba, mask=rgba.getchannel("A"))
        sheet.paste(b2.resize((cell, cell), Image.LANCZOS), (i * cell, cell + 8))
    sheet.save(OUT / "compare_final.png")
    sheet.save(REPO / "monster-compare.png")
    print("compare ->", OUT / "compare_final.png")


if __name__ == "__main__":
    main()
