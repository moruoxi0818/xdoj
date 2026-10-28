# -*- coding: utf-8 -*-
"""题面 PDF -> 文本（优先文字层），必要时渲染成图片"""

import os
import re

import pymupdf


def pdf_to_text(pdf_bytes, max_pages=6):
    """返回 (text, images)；有文字层就只给 text，没有就渲染图片"""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    parts = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        parts.append(page.get_text("text"))
    text = "\n".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) >= 60:
        doc.close()
        return text, []

    # 扫描版：渲染成图片
    imgs = []
    tmpdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "shots")
    os.makedirs(tmpdir, exist_ok=True)
    stamp = abs(hash(pdf_bytes)) % 10 ** 8
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        p = os.path.join(tmpdir, f"pdf_{stamp}_{i}.png")
        pix.save(p)
        imgs.append(p)
    doc.close()
    return "", imgs


def parse_samples(text):
    """从题面里抽出 (输入, 输出) 样例对，抽不干净就返回空列表"""
    if not text:
        return []
    t = text.replace("\u3000", " ")
    # 找出所有「输入样例N：」和「输出样例N：」的位置
    marks = []
    for m in re.finditer(r"(输入|输出)\s*样例\s*\d*\s*[:：]?", t):
        marks.append((m.start(), m.end(), m.group(1)))
    pairs = []
    for i, (s, e, kind) in enumerate(marks):
        if kind != "输入":
            continue
        nxt = marks[i + 1] if i + 1 < len(marks) else None
        if not nxt or nxt[2] != "输出":
            continue
        raw_in = t[e:nxt[0]]
        nxt2 = marks[i + 2] if i + 2 < len(marks) else None
        end = nxt2[0] if nxt2 else len(t)
        raw_out = t[nxt[1]:end]
        cin = _clean_block(raw_in)
        cout = _clean_block(raw_out)
        if cin and cout:
            pairs.append((cin, cout))
    return pairs[:3]


def _clean_block(s):
    if not s:
        return ""
    lines = []
    for ln in s.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        # 遇到「说明/提示/备注/评分」等非样例内容就停
        if re.match(r"^(备注|说明|提示|注意|数据范围|评分|本题|其中)", ln):
            break
        lines.append(ln)
        if len(lines) >= 8:
            break
    out = "\n".join(lines).strip()
    return out


if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "rb") as f:
        txt, imgs = pdf_to_text(f.read())
    print(txt[:1500])
    print("--- samples ---")
    for a, b in parse_samples(txt):
        print("IN :", repr(a))
        print("OUT:", repr(b))
