from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    content: str

class ArticleCreate(ArticleBase):
    author_id: int

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class Article(ArticleBase):
    author_id: int
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
