"""持仓管理模块

JSON 文件持久化，支持增删改查。
存储路径：backend/data/portfolio_data.json
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from threading import Lock

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio_data.json")
_lock = Lock()


def _read() -> dict:
    """读取持仓数据"""
    if not os.path.exists(PORTFOLIO_FILE):
        return {"holdings": [], "updated_at": ""}
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"holdings": [], "updated_at": ""}


def _write(data: dict):
    """写入持仓数据"""
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_holdings() -> dict:
    """获取全部持仓"""
    with _lock:
        return _read()


def add_holding(code: str, name: str, cost_price: float, quantity: int,
                notes: str = "") -> dict:
    """添加一条持仓"""
    with _lock:
        data = _read()
        holding = {
            "id": uuid.uuid4().hex[:8],
            "code": code.strip().zfill(6),
            "name": name.strip(),
            "cost_price": round(float(cost_price), 2),
            "quantity": int(quantity),
            "notes": notes.strip(),
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        data["holdings"].append(holding)
        data["updated_at"] = datetime.now().isoformat()
        _write(data)
        return holding


def update_holding(holding_id: str, **kwargs) -> dict | None:
    """更新一条持仓"""
    with _lock:
        data = _read()
        for h in data["holdings"]:
            if h["id"] == holding_id:
                if "cost_price" in kwargs:
                    h["cost_price"] = round(float(kwargs["cost_price"]), 2)
                if "quantity" in kwargs:
                    h["quantity"] = int(kwargs["quantity"])
                if "notes" in kwargs:
                    h["notes"] = kwargs["notes"].strip()
                if "name" in kwargs:
                    h["name"] = kwargs["name"].strip()
                data["updated_at"] = datetime.now().isoformat()
                _write(data)
                return h
        return None


def delete_holding(holding_id: str) -> bool:
    """删除一条持仓"""
    with _lock:
        data = _read()
        before = len(data["holdings"])
        data["holdings"] = [h for h in data["holdings"] if h["id"] != holding_id]
        if len(data["holdings"]) == before:
            return False
        data["updated_at"] = datetime.now().isoformat()
        _write(data)
        return True


def clear_holdings() -> int:
    """清空全部持仓"""
    with _lock:
        count = len(_read()["holdings"])
        _write({"holdings": [], "updated_at": datetime.now().isoformat()})
        return count
