from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, role_id: int) -> Optional[Role]:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.id == role_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Role]:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.name == name)
            .first()
        )

    def list_all(self) -> list[Role]:
        return self.db.query(Role).options(joinedload(Role.permissions)).order_by(Role.id).all()

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def save(self, role: Role) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.commit()
