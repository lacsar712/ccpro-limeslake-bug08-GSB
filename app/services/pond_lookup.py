"""池排序、抽屉近班与页脚计数。

约定：一切数据都必须落到「当前厂区 / 当前池」上——
排序用自然序（P-2 在 P-10 前），抽屉只取本池近班，页脚只数本厂池。
"""

from __future__ import annotations

import re

from app.models import Pond
from app.services.rules import latest_batch_for_pond

# 把池号切成 文本/数字 交替的片段：P-10 -> ("p-", 10)，P-2 -> ("p-", 2)
_NUM_RE = re.compile(r"(\d+)")


def natural_sort_key(code: str | None) -> tuple:
    """自然排序键：数字段按数值比，其余按文本比。

    P-1, P-2, P-10 -> 1, 2, 10（而不是字符串序的 1, 10, 2）。
    """
    parts = _NUM_RE.split((code or "").lower())
    return tuple(int(part) if part.isdigit() else part for part in parts if part != "")


def sort_ponds(ponds: list[Pond]) -> list[Pond]:
    """按池号自然序排列（同号时回退到 id，保证顺序稳定）。"""
    return sorted(ponds, key=lambda p: (natural_sort_key(p.code), p.id or 0))


def drawer_batch_for(pond: Pond):
    """抽屉近班：只认被点瓦片自己那口池的最近批次。

    不看邻号、不写任何进程级状态，所以两人同时点相邻池时
    各请求各自计算，不会互相串笔。
    """
    if pond is None:
        return None
    return latest_batch_for_pond(pond)


def footer_pond_count(plant_id: int | None) -> int:
    """页脚池数：只统计当前厂区的池，别厂不计，重复 id 只算一次。"""
    if plant_id is None:
        return 0
    return Pond.query.filter_by(plant_id=plant_id).distinct().count()
