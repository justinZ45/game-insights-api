from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .game_publisher import GamePublisher


class Publisher(Base):
    """Lookup table - represents a single unique entry per game Publisher"""

    __tablename__ = "publishers"

    game_links: Mapped[list["GamePublisher"]] = relationship(
        "GamePublisher", backref="publisher", cascade="all, delete-orphan"
    )

    publisher_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
