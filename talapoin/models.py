from __future__ import annotations

from typing import List

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

from datetime import datetime, timezone

import re

class Model(DeclarativeBase):
    pass

class Page(Model):
    __tablename__ = 'page'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), default='')
    slug = Column(String(255), nullable=False, unique=True)
    content = Column(Text)
    description = Column(Text)
    draft = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(tz=timezone.utc), onupdate=datetime.now(tz=timezone.utc))

    def __repr__(self):
        return f"<Page(title='{self.title}', slug='{self.slug}')>"

EntryTag = Table(
    'entry_to_tag',
    Model.metadata,
    Column('entry_id', ForeignKey("entry.id"), primary_key=True),
    Column('tag_id', ForeignKey("tag.id"), primary_key=True)
)

class Tag(Model):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    
    entries: Mapped[List[Entry]] = relationship(secondary=EntryTag, back_populates="tags")

class Entry(Model):
    __tablename__ = "entry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), default=None)
    entry: Mapped[str] = mapped_column(String(Text), nullable=False)
    mastodon_uri: Mapped[str] = mapped_column(String(255), default=None)
    bluesky_uri: Mapped[str] = mapped_column(String(255), default=None)
    toot: Mapped[str] = mapped_column(String(Text), nullable=False)
    article: Mapped[int] = mapped_column(default=0)
    draft: Mapped[int] = mapped_column(default=0)
    closed: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc), onupdate=datetime.now(tz=timezone.utc))
    tags: Mapped[List[Tag]] = relationship(secondary=EntryTag, back_populates='entries')

    @property
    def slug(self):
        if self.title:
            return re.sub(r'[^-A-Za-z0-9,]', '_', self.title.lower())
        else:
            return self.id

    @property
    def canonicalUrl(self):
        return f'/{self.created_at.year}/{self.created_at.month}/{self.created_at.day}/{self.slug}'
