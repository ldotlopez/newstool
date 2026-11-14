---
paths:
  - "newstool/db.py"
  - "newstool/models.py"
  - "scripts/**"
  - "private/**"
---

# Database & ORM Conventions

- **DTO Boundary Isolation:** SQLAlchemy ORM models MUST NOT leak outside the database / data access layer (`newstool/db.py`).
  - Convert data passing into or out of the DB layer using `@dataclass(slots=True)` DTOs (`newstool/models.py`).
  - Every SQLAlchemy model must implement three explicit methods:
    - `from_dto(cls, dto: DTOType) -> Self`: Class method to instantiate a new DB model from a DTO.
    - `to_dto(self) -> DTOType`: Instance method to export model state to its corresponding `@dataclass` DTO.
    - `update(self, dto: DTOType) -> None`: Instance method to update all fields on the DB object from the DTO except the primary key/ID. Use explicit field assignment (`self.field = dto.field`) rather than reflective loops or `setattr` iterations.
- **Database-Native Integrity:** Prefer database-level constraints and triggers over ORM-level or Python-level validation hooks.
  - Define `CheckConstraint`, `UniqueConstraint`, and foreign key cascade rules directly in SQLAlchemy model table definitions so they execute natively in SQL.
- **No Migrations Framework:** The schema is created, never migrated. Changes to existing tables or stored data need a one-shot migration plus its test in `private/`, which is git-ignored: they run once in production and are never committed.
- **Content on Disk:** Annotation values and item and document contents are stored as files under `content_dir`, not in the DB (ADR 0004).

## DTO, Protocol & ORM Implementation Reference

```python
from dataclasses import dataclass
from typing import Protocol, Self
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Internal DTO based on dataclass (used specifically for DB isolation)
@dataclass(slots=True)
class UserDTO:
    id: int | None = None
    email: str | None = None
    username: str | None = None


# Decoupling Protocol
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> UserDTO | None: ...
    def save(self, dto: UserDTO) -> UserDTO: ...


# ORM Implementation
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    @classmethod
    def from_dto(cls, dto: UserDTO) -> Self:
        """Create a new DB instance from a DTO."""
        if dto.email is None or dto.username is None:
            raise ValueError("Email and username are required to instantiate a User")
        return cls(email=dto.email, username=dto.username)

    def to_dto(self) -> UserDTO:
        """Export model state to a Dataclass DTO."""
        return UserDTO(id=self.id, email=self.email, username=self.username)

    def update(self, dto: UserDTO) -> None:
        """Update all fields on the DB model from the DTO except the ID.

        Explicitly set fields directly rather than using dynamic field iteration.
        """
        if dto.email is not None:
            self.email = dto.email
        if dto.username is not None:
            self.username = dto.username
```
