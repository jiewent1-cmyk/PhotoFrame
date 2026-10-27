#!/usr/bin/env python3
"""压缩 docs/assets/ 下的图片并生成 WebP 版本；把新截图处理成网页用图。

用法: python3 tools/optimize_assets.py <新截图目录>
新截图目录需含 grid.png 与 export.png（3000x1716，Mac 浅色模式窗口内容）。

- 现有 JPG: quality=82, progressive, optimize 重新压缩，并输出同名 .webp (q82, method=6)
- icon.png: 无损优化，另输出 icon.webp (lossless)
- grid.png  -> shot-grid.jpg / .webp   (长边 2000)
- export.png-> shot-export.jpg / .webp (裁「预览 + 导出卡片」区域，长边 2000)
  export.png 里导出卡片中的临时文件夹路径一行会被涂掉。
"""
import os
import sys

from PIL import Image, ImageDraw

ASSETS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "assets")
)
JPG = dict(quality=82, progressive=True, optimize=True)
WEBP = dict(quality=82, method=6)


def save_pair(im, base):
    im.save(base + ".jpg", "JPEG", **JPG)
    im.save(base + ".webp", "WEBP", **WEBP)


def main(src_dir):
    report = []

    # 1) 现有 JPG 重新压缩 + WebP
    for name in sorted(os.listdir(ASSETS)):
        if not name.endswith(".jpg"):
            continue
        path = os.path.join(ASSETS, name)
        before = os.path.getsize(path)
        im = Image.open(path)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(path, "JPEG", **JPG)
        # demo-lake.jpg 只被 JS canvas 引用，不给 webp
        wsize = 0
        if name != "demo-lake.jpg":
            im.save(os.path.join(ASSETS, name[:-4] + ".webp"), "WEBP", **WEBP)
            wsize = os.path.getsize(os.path.join(ASSETS, name[:-4] + ".webp"))
        report.append((name, before, os.path.getsize(path), wsize))

    # 2) icon.png 无损优化 + WebP
    icon = os.path.join(ASSETS, "icon.png")
    before = os.path.getsize(icon)
    im = Image.open(icon)
    im.save(icon, "PNG", optimize=True, compress_level=9)
    im.save(os.path.join(ASSETS, "icon.webp"), "WEBP", lossless=True, method=6)
    report.append(("icon.png", before, os.path.getsize(icon), os.path.getsize(os.path.join(ASSETS, "icon.webp"))))

    # 3) 网格截图 -> shot-grid
    grid = Image.open(os.path.join(src_dir, "grid.png")).convert("RGB")
    grid = grid.resize((2000, round(grid.height * 2000 / grid.width)), Image.LANCZOS)
    save_pair(grid, os.path.join(ASSETS, "shot-grid"))
    report.append(("shot-grid (new)", 0, os.path.getsize(os.path.join(ASSETS, "shot-grid.jpg")),
                   os.path.getsize(os.path.join(ASSETS, "shot-grid.webp"))))

    # 4) 导出截图 -> shot-export：涂掉临时路径一行与顶部被截断的卡片残片，再裁「预览 + 导出卡片」
    ex = Image.open(os.path.join(src_dir, "export.png")).convert("RGB")
    d = ImageDraw.Draw(ex)
    d.rectangle([2224, 225, 2976, 336], fill=(236, 236, 236))   # 侧栏顶部截断卡片残片 -> 侧栏底色
    d.rectangle([2318, 935, 2872, 966], fill=(244, 244, 244))   # 导出卡片里的临时文件夹路径
    ex = ex.crop((940, 225, 3000, 1600))
    ex = ex.resize((2000, round(ex.height * 2000 / ex.width)), Image.LANCZOS)
    save_pair(ex, os.path.join(ASSETS, "shot-export"))
    report.append(("shot-export (new)", 0, os.path.getsize(os.path.join(ASSETS, "shot-export.jpg")),
                   os.path.getsize(os.path.join(ASSETS, "shot-export.webp"))))

    print(f"{'file':<22}{'before':>10}{'jpg':>10}{'webp':>10}")
    total_before = total_after = 0
    for name, b, j, w in report:
        total_before += b
        total_after += min(j, w)
        print(f"{name:<22}{b:>10}{j:>10}{w:>10}")
    print(f"{'TOTAL (min per file)':<22}{total_before:>10}{total_after:>10}")
    print("dims:", {n: Image.open(os.path.join(ASSETS, n + ".jpg")).size
                    for n in ("shot-grid", "shot-export")})


if __name__ == "__main__":
    main(sys.argv[1])
