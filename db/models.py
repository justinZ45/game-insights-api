from sqlalchemy import Integer, String, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional


class Base(DeclarativeBase):
    pass


class Game(Base):
    """Represents a single video game entry"""

    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True)
    lengths: Mapped[list["GameLength"]] = relationship(
        "GameLength", backref="game", cascade="all, delete-orphan"
    )
    genres: Mapped[list["GameGenre"]] = relationship(
        "GameGenre", backref="game", cascade="all, delete-orphan"
    )
    publishers: Mapped[list["GamePublisher"]] = relationship(
        "GamePublisher", backref="game", cascade="all, delete-orphan"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_handheld: Mapped[Optional[bool]]
    max_players: Mapped[Optional[int]]
    is_multiplatform: Mapped[Optional[bool]]
    is_online: Mapped[Optional[bool]]
    is_licensed: Mapped[Optional[bool]]
    is_sequel: Mapped[Optional[bool]]
    review_score: Mapped[Optional[int]]
    sales: Mapped[Optional[float]]
    used_price: Mapped[Optional[float]]
    console: Mapped[Optional[str]] = mapped_column(String(255))
    esrb_rating: Mapped[Optional[str]] = mapped_column(String(5))
    is_re_release: Mapped[Optional[bool]]
    release_year: Mapped[Optional[int]]


class GameLength(Base):
    """
    Represents a single entry for a game's lengths.

    References games table (one to many relationship).
    """

    __tablename__ = "game_lengths"

    game_lengths_id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE")
    )
    playstyle: Mapped[Optional[str]] = mapped_column(String(255))
    avg_hours: Mapped[Optional[float]] = mapped_column(Float)
    leisure_hours: Mapped[Optional[float]] = mapped_column(Float)
    median_hours: Mapped[Optional[float]] = mapped_column(Float)
    rushed_hours: Mapped[Optional[float]] = mapped_column(Float)
    num_players_polled: Mapped[Optional[int]] = mapped_column(Integer)


class Genre(Base):
    """Lookup table - represents a single unique entry per game Genre"""

    __tablename__ = "genres"

    game_links: Mapped[list["GameGenre"]] = relationship(
        "GameGenre", backref="genre", cascade="all, delete-orphan"
    )

    genre_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Publisher(Base):
    """Lookup table - represents a single unique entry per game Publisher"""

    __tablename__ = "publishers"

    game_links: Mapped[list["GamePublisher"]] = relationship(
        "GamePublisher", backref="publisher", cascade="all, delete-orphan"
    )

    publisher_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class GameGenre(Base):
    """Junction table - (map game id to genre id for lookup)"""

    __tablename__ = "game_genres"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.genre_id", ondelete="CASCADE"), primary_key=True
    )


class GamePublisher(Base):
    """Junction table - (map game id to publisher id for lookup)"""

    __tablename__ = "game_publishers"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True
    )
    publisher_id: Mapped[int] = mapped_column(
        ForeignKey("publishers.publisher_id", ondelete="CASCADE"), primary_key=True
    )
