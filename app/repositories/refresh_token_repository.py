from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.flush()
        self.db.refresh(refresh_token)
        return refresh_token

    def get_by_token_hash(
        self, token_hash: str, with_user_permissions: bool = False
    ) -> Optional[RefreshToken]:
        query = self.db.query(RefreshToken).filter(RefreshToken.token == token_hash)
        if with_user_permissions:
            query = query.options(
                joinedload(RefreshToken.user).joinedload(User.role).joinedload(Role.permissions)
            )
        return query.first()

    def save(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.flush()
        self.db.refresh(refresh_token)
        return refresh_token

    def revoke_family(self, family_id: str) -> None:
        self.db.query(RefreshToken).filter(RefreshToken.family_id == family_id).update(
            {"revoked": True}, synchronize_session=False
        )
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()
