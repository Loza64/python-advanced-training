from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id",ForeignKey("permissions.id", ondelete="CASCADE"),primary_key=True,
    ),
)