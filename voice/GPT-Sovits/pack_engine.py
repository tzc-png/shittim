#!/usr/bin/env python3
"""
pack_engine.py — 从 GPT-SoVITS 项目中提取推理所需文件
生成一个完全独立的 plana_engine/ 目录，不再依赖 GPT-SoVITS 项目

用法：
    python3 pack_engine.py \
        --src  ~/my_software/GPT-SoVITS \
        --out  ~/my_software/shittim/plana_engine
"""

import argparse
import os
import shutil
import sys


# ── 需要从 GPT_SoVITS/ 子目录拷出的文件/目录 ──────────────────────────────────
# 格式：(相对于 GPT_SoVITS/ 的路径, 是否整个目录)
GPTSOVITS_ITEMS = [
    # cnhubert 加载器（我们会用 transformers 替代，但先拷备用）
    ("feature_extractor/cnhubert.py",         False),
    ("feature_extractor/__init__.py",         False),

    # SoVITS 模型定义
    ("module",                                True),

    # AR/GPT 模型定义
    ("AR/models/t2s_lightning_module.py",    False),
    ("AR/models/t2s_model.py",               False),
    ("AR/models/__init__.py",                False),
    ("AR/modules/transformer.py",            False),
    ("AR/modules/embedding.py",              False),
    ("AR/modules/activation.py",            False),
    ("AR/modules/patched_mha_with_cache.py", False),
    ("AR/modules/__init__.py",               False),
    ("AR/__init__.py",                       False),

    # text 处理（日语 G2P）
    ("text/__init__.py",                     False),
    ("text/symbols.py",                      False),
    ("text/symbols2.py",                     False),
    ("text/japanese.py",                     False),
    ("text/ja_userdic",                      True),   # 整个目录
]

# ── 需要从 pretrained_models/ 拷出的模型目录 ──────────────────────────────────
PRETRAINED_ITEMS = [
    "chinese-hubert-base",   # cnhubert 模型权重
]


def copy_item(src_path, dst_path, is_dir):
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if is_dir:
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)
        if os.path.exists(src_path):
            shutil.copytree(src_path, dst_path)
            print(f"  ✓ {dst_path}/")
        else:
            print(f"  ✗ 跳过（不存在）：{src_path}")
    else:
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"  ✓ {dst_path}")
        else:
            print(f"  ✗ 跳过（不存在）：{src_path}")


def pack(src_root: str, out_dir: str):
    src_gptsovits = os.path.join(src_root, "GPT_SoVITS")
    src_pretrained = os.path.join(src_gptsovits, "pretrained_models")

    os.makedirs(out_dir, exist_ok=True)

    # ── 1. 拷 GPT_SoVITS 内部模块 ──────────────────────────────────────────
    print(f"\n[1/3] 拷贝模型定义文件 → {out_dir}/")
    for rel_path, is_dir in GPTSOVITS_ITEMS:
        src = os.path.join(src_gptsovits, rel_path)
        dst = os.path.join(out_dir, rel_path)
        copy_item(src, dst, is_dir)

    # ── 2. 拷 chinese-hubert-base 权重 ────────────────────────────────────
    print(f"\n[2/3] 拷贝 chinese-hubert-base → {out_dir}/pretrained_models/")
    for name in PRETRAINED_ITEMS:
        src = os.path.join(src_pretrained, name)
        dst = os.path.join(out_dir, "pretrained_models", name)
        copy_item(src, dst, True)

    # ── 3. 生成 __init__.py 确保包结构完整 ────────────────────────────────
    print(f"\n[3/3] 补全包结构...")
    for pkg_dir in ["feature_extractor", "module", "AR", "AR/models",
                    "AR/modules", "text"]:
        init = os.path.join(out_dir, pkg_dir, "__init__.py")
        if not os.path.exists(init):
            open(init, "w").close()
            print(f"  ✓ 创建空 {init}")

    # ── 4. 生成修改后的 cnhubert.py（用 transformers 直接加载，去掉多余依赖）
    print(f"\n[4/4] 生成精简版 cnhubert.py...")
    cnhubert_content = '''\
"""
精简版 cnhubert.py
直接用 transformers 加载，不依赖 GPT-SoVITS 其他模块
"""
import torch
from transformers import HubertModel, Wav2Vec2FeatureExtractor

cnhubert_base_path = ""


class CNHubert(torch.nn.Module):
    def __init__(self, base_path: str):
        super().__init__()
        self.model = HubertModel.from_pretrained(base_path)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(base_path)

    def forward(self, x):
        return self.model(x)


def get_model():
    assert cnhubert_base_path, "请先设置 cnhubert_base_path"
    model = CNHubert(cnhubert_base_path)
    model.eval()
    return model
'''
    dst = os.path.join(out_dir, "feature_extractor", "cnhubert.py")
    with open(dst, "w") as f:
        f.write(cnhubert_content)
    print(f"  ✓ 精简版 {dst}")

    # ── 完成 ───────────────────────────────────────────────────────────────
    print(f"\n完成！独立引擎目录：{out_dir}")
    print("\n目录结构：")
    for root, dirs, files in os.walk(out_dir):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        level = root.replace(out_dir, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(root, f))
            print(f"{indent}  {f}  ({size/1024:.1f}KB)")

    print(f"""
部署时只需把 plana_engine/ 整个目录拷到目标机器，
然后设置：
    PLANA_ENGINE_DIR=/path/to/plana_engine
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="GPT-SoVITS 项目根目录")
    parser.add_argument("--out", required=True, help="输出目录")
    args = parser.parse_args()
    pack(os.path.expanduser(args.src), os.path.expanduser(args.out))
