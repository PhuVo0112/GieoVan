from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class PoemStar(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    poem_id: int = Field(foreign_key="poem.id", primary_key=True)
    starred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    poems: List["Poem"] = Relationship(back_populates="author")
    starred_poems: List["Poem"] = Relationship(back_populates="starred_by_users", link_model=PoemStar)

class Poem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(nullable=False)
    author_id: Optional[int] = Field(default=None, foreign_key="user.id", nullable=True)
    is_public: bool = Field(default=False)
    views: int = Field(default=0)
    likes: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author: Optional[User] = Relationship(back_populates="poems")
    starred_by_users: List["User"] = Relationship(back_populates="starred_poems", link_model=PoemStar)
