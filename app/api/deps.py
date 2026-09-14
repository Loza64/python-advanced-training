from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.services.category_service import CategoryService
from app.services.product_service import ProductService


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	except SQLAlchemyError:
		db.rollback()
		raise
	finally:
		db.close()


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
	return CategoryService(CategoryRepository(db))


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
	return ProductService(ProductRepository(db), CategoryRepository(db))

# Aquí más adelante también irían dependencias de autenticación (JWT, etc.)