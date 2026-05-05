"""章节切分与检索块分块。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str
    book_title: str
    chapter_title: str
    section_title: str
    text: str
    chunk_order: int
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None


CHAPTER_PATTERNS = [
    re.compile(r"第[零一二三四五六七八九十百千\d]+章\s*.{0,30}"),
    re.compile(r"第[零一二三四五六七八九十百千\d]+节\s*.{0,30}"),
    re.compile(r"[一二三四五六七八九十]、\s*.{0,30}"),
]


def split_by_chapters(text: str) -> list[dict]:
    """按章节标题切分文本，返回 [{chapter_title, section_title, text}, ...]。

    使用正则识别"第X章""第X节"等标题模式。
    """
    merged = "(" + "|".join(p.pattern for p in CHAPTER_PATTERNS) + ")"
    parts = re.split(merged, text)
    sections: list[dict] = []
    current_chapter = "前言"
    current_section = ""

    for i, part in enumerate(parts):
        if not part or not part.strip():
            continue
        match = False
        for p in CHAPTER_PATTERNS:
            if p.fullmatch(part.strip()):
                match = True
                break
        if match:
            if "章" in part:
                current_chapter = part.strip()
                current_section = ""
            elif "节" in part or part.strip().startswith(("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")):
                current_section = part.strip()
        else:
            sections.append({
                "chapter_title": current_chapter,
                "section_title": current_section,
                "text": part.strip(),
            })

    return sections


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """将长文本切分为固定大小（字数）的检索块。

    按句号、换行等自然边界切分，避免截断句子。
    """
    chunks: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= chunk_size and char in "。！？\n":
            chunks.append(current.strip())
            current = ""
    if current.strip():
        chunks.append(current.strip())
    return chunks


def build_chunk_records(
    book_meta: dict,
    sections: list[dict],
    chunk_size: int = 500,
) -> list[Chunk]:
    """构建完整的 Chunk 记录列表，含前后相邻指针。"""
    records: list[Chunk] = []
    order = 0

    for sec in sections:
        text_chunks = chunk_text(sec["text"], chunk_size)
        for t in text_chunks:
            chunk_id = f"{book_meta.get('book_id', 'unknown')}_{order:04d}"
            records.append(Chunk(
                chunk_id=chunk_id,
                book_title=book_meta.get("book_title", ""),
                chapter_title=sec["chapter_title"],
                section_title=sec["section_title"],
                text=t,
                chunk_order=order,
            ))
            order += 1

    for i, rec in enumerate(records):
        if i > 0:
            rec.prev_chunk_id = records[i - 1].chunk_id
        if i < len(records) - 1:
            rec.next_chunk_id = records[i + 1].chunk_id

    return records
