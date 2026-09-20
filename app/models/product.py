from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity

if TYPE_CHECKING:
    from app.models.category import Category

class Product(BaseEntity):
    __tablename__ = "products"
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    # raise_on_sql: category es requerido en ProductResponse (incluso en
    # listados), así que el repositorio SIEMPRE debe pedirlo con joinedload.
    # Este flag convierte un N+1 silencioso en un error explícito si alguna
    # query nueva se olvida de hacerlo.
    category: Mapped[Category] = relationship(
        back_populates="products", lazy="raise_on_sql"
    )
    
    
