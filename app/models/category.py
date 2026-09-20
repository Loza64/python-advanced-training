from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity

if TYPE_CHECKING:
    from app.models.product import Product


class Category(BaseEntity):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # raise_on_sql: products nunca se necesita en las respuestas actuales;
    # si algún día se requiere, debe pedirse con eager load explícito.
    products: Mapped[list[Product]] = relationship(
        back_populates="category", lazy="raise_on_sql"
    )
    
