"""池排序与近班查找。"""

from __future__ import annotations

import re

from app.models import Pond
from app.services.rules import latest_batch_for_pond

_SPLIT_DIGITS = re.compile(r"(\d+)")


def _natural_key(code: str | None) -> tuple:
    """池号排序键：文本段按字面值、数字段按数值比，保证 2 排在 10 前。"""
    key = []
    for chunk in _SPLIT_DIGITS.split(code or ""):
        if chunk.isdigit():
            key.append((1, int(chunk)))
        else:
            key.append((0, chunk.casefold()))
    return tuple(key)


def sort_ponds_natural(ponds: list[Pond]) -> list[Pond]:
    """按池号自然序排：P-2 在 P-10 前，不再按字符串排。"""
    return sorted(ponds, key=lambda p: (_natural_key(p.code), p.code or ""))


def drawer_batch_for(pond: Pond):
    """抽屉近班：只取本池最近批次；不读邻号、不写共享状态，并发点击互不串班。"""
    return latest_batch_for_pond(pond)


def footer_pond_count(active_plant_id: int | None) -> int:
    """页脚池座数：只算当前厂的池，不串别厂、不重复；无厂区时为零。"""
    if active_plant_id is None:
        return 0
    return Pond.query.filter_by(plant_id=active_plant_id).count()
