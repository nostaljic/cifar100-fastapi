from sqlalchemy.orm import declarative_base
from app.infrastructure.Database import engine


EntityMeta = declarative_base()


def init() -> None:
    EntityMeta.metadata.create_all(bind=engine)
