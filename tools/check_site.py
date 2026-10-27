#!/usr/bin/env python3
"""检查 docs/index.html：assets 引用是否都存在、id 是否重复、页内锚点是否对得上、标签是否闭合、img 属性是否齐全。

用法: python3 tools/check_site.py
"""
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PAGE = os.path.join(ROOT, "docs", "index.html")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = []
        self.anchors = []
        self.assets = []
        self.imgs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))
        if "id" in a:
            self.ids.append(a["id"])
        for key in ("src", "href", "srcset"):
            if key in a:
                for part in a[key].split(","):
                    url = part.strip().split(" ")[0]
                    if url.startswith("assets/"):
                        self.assets.append(url)
                    if key == "href" and url.startswith("#") and len(url) > 1:
                        self.anchors.append(url[1:])
        if tag == "img":
            self.imgs.append((a, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: 多余的 </{tag}>")
        elif self.stack[-1][0] != tag:
            self.errors.append(f"line {self.getpos()[0]}: </{tag}> 与未闭合的 <{self.stack[-1][0]}> (line {self.stack[-1][1][0]}) 不匹配")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
        else:
            self.stack.pop()


def main():
    html = open(PAGE, encoding="utf-8").read()
    c = Checker()
    c.feed(html)
    c.close()

    # CSS / JS 里引用的 assets
    for m in re.finditer(r"""url\((['"]?)(assets/[^)'"]+)\1\)""", html):
        c.assets.append(m.group(2))
    for m in re.finditer(r"""['"](assets/[^'"]+)['"]""", html):
        c.assets.append(m.group(1))

    bad = 0
    missing = sorted({a for a in c.assets if not os.path.isfile(os.path.join(ROOT, "docs", a))})
    if missing:
        bad += len(missing)
        for m in missing:
            print(f"MISSING  {m}")
    else:
        print(f"OK  assets 引用全部存在（{len(set(c.assets))} 个）")

    dup = {i for i in c.ids if c.ids.count(i) > 1}
    if dup:
        bad += len(dup)
        print(f"DUPLICATE id: {sorted(dup)}")
    else:
        print(f"OK  id 无重复（{len(c.ids)} 个）")

    dead = [a for a in set(c.anchors) if a not in c.ids]
    if dead:
        bad += len(dead)
        print(f"DEAD anchor: {sorted(dead)}")
    else:
        print(f"OK  页内锚点都能对上（{len(set(c.anchors))} 个）")

    if c.stack:
        bad += len(c.stack)
        print(f"UNCLOSED: {[(t, p[0]) for t, p in c.stack]}")
    if c.errors:
        bad += len(c.errors)
        for e in c.errors:
            print("TAG     ", e)
    if not c.stack and not c.errors:
        print("OK  标签闭合")

    for a, pos in c.imgs:
        probs = [k for k in ("width", "height", "alt") if k not in a]
        if probs:
            bad += 1
            print(f"IMG line {pos[0]}: 缺 {probs} -> {a.get('src')}")
    print(f"OK  {len(c.imgs)} 个 <img> 都有 width/height/alt" if not bad else "")

    # 未被引用的 assets 文件（供清理参考，不算错误）
    used = {os.path.basename(a) for a in c.assets}
    unused = sorted(f for f in os.listdir(os.path.join(ROOT, "docs", "assets")) if f not in used)
    print("未被引用的 assets 文件:", unused or "无")

    print("FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
