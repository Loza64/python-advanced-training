from typing import TypeVar

from sqlalchemy import Select

ModelT = TypeVar("ModelT")


def apply_sort(query: Select, model: type[ModelT], sort: list[str], allowed_fields: set[str]) -> Select:
    for item in sort:
        field_name, direction = item.split(",")
        if field_name not in allowed_fields:
            raise ValueError(f"Unsupported sort field: {field_name}")

        column = getattr(model, field_name)
        query = query.order_by(column.desc() if direction == "desc" else column.asc())

    return query