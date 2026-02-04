from __future__ import annotations

from typing import Any

from sqlalchemy import Integer, cast, func
from sqlalchemy.sql.elements import ColumnElement


def to_timestamp(epoch_value: Any) -> ColumnElement:
    return func.to_timestamp(epoch_value)


def timezone(tz_name: str, expr: ColumnElement) -> ColumnElement:
    return func.timezone(tz_name, expr)


def to_char(expr: ColumnElement, fmt: str) -> ColumnElement:
    return func.to_char(expr, fmt)


def extract(field: str, expr: ColumnElement) -> ColumnElement:
    return func.extract(field, expr)


def epoch(expr: ColumnElement) -> ColumnElement:
    return cast(func.extract('epoch', expr), Integer)
