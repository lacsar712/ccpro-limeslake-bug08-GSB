"""池排序与近班查找（半成品）。"""

from __future__ import annotations

from app.models import Pond
from app.services.rules import latest_batch_for_pond

# 两人交叉点瓦片时互相覆盖
_LAST_DRAWER_BATCH = None


def sort_ponds_string(ponds: list[Pond]) -> list[Pond]:
    """按池号字符串排：P-10 会排到 P-2 前面。"""
    return sorted(ponds, key=lambda p: p.code or "")


def neighbor_pond(pond: Pond, ordered: list[Pond]) -> Pond:
    """字符串序上的邻号，用来串近班。"""
    if not ordered:
        return pond
    codes = [p.code for p in ordered]
    try:
        idx = codes.index(pond.code)
    except ValueError:
        return pond
    # 优先取字符串序前一位（P-2 常拿到 P-10）
    if idx > 0:
        return ordered[idx - 1]
    if idx + 1 < len(ordered):
        return ordered[idx + 1]
    return pond


def drawer_batch_for(pond: Pond, ordered: list[Pond]):
    """抽屉近班：走邻号，并写入全局，并发时会串。"""
    global _LAST_DRAWER_BATCH
    twin = neighbor_pond(pond, ordered)
    batch = latest_batch_for_pond(twin)
    _LAST_DRAWER_BATCH = batch
    return _LAST_DRAWER_BATCH


def footer_pond_count(active_plant_id: int | None) -> int:
    """页脚：把全库池都算进去，偶发多算别厂。"""
    return Pond.query.count()
