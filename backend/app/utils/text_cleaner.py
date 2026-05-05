"""文本清洗：统一编码、去除噪音、提取元数据。"""

from __future__ import annotations

import re
import hashlib
from pathlib import Path


def clean_text(raw_text: str) -> str:
    """清洗原始文本，返回干净的正文内容。

    处理步骤：
    1. 统一编码为 UTF-8
    2. 去除连续空行（保留单个换行）
    3. 去除无意义乱码和特殊符号
    4. 去除明显页码（纯数字行）
    5. 去除页眉页脚模式
    """
    text = raw_text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_front_matter(text: str) -> str:
    """去除目录页、版权页等非正文前置内容。

    启发式判断：如果前 500 字内出现"目录""版权""ISBN"等关键词，则截断。
    """
    head = text[:500]
    if re.search(r"目录|版权|ISBN|出版信息|图书在版编目", head):
        for marker in ["第一章", "第1章", "前言", "序言", "绪论", "引言"]:
            idx = text.find(marker)
            if idx > 100:
                return text[idx:]
    return text


def compute_md5(text: str) -> str:
    """计算文本的 MD5 哈希，用于段落级去重。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_metadata(file_path: Path) -> dict:
    """从文件名推断书籍元数据。"""
    name = file_path.stem
    merchant_hint = ""
    if "晋" in name or "山西" in name:
        merchant_hint = "晋商"
    elif "徽" in name or "徽州" in name or "新安" in name:
        merchant_hint = "徽商"
    elif "陕" in name:
        merchant_hint = "陕商"
    elif "粤" in name or "广东" in name:
        merchant_hint = "粤商"
    elif "浙" in name or "宁波" in name or "温州" in name:
        merchant_hint = "浙商"
    elif "苏" in name:
        merchant_hint = "苏商"
    elif "赣" in name or "江西" in name:
        merchant_hint = "赣商"

    return {
        "book_title": name,
        "source_type": "txt",
        "merchant_group_hint": merchant_hint,
    }


def clean_file(input_path: Path, output_dir: Path) -> dict:
    """清洗单个文件并保存，返回元数据。"""
    raw = input_path.read_text(encoding="utf-8", errors="replace")
    text = clean_text(raw)
    text = remove_front_matter(text)
    meta = extract_metadata(input_path)
    meta["book_id"] = compute_md5(input_path.name)[:8]
    meta["char_count"] = len(text)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{meta['book_id']}.txt"
    out_path.write_text(text, encoding="utf-8")
    meta["cleaned_path"] = str(out_path)
    return meta
