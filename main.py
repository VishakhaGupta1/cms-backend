from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import engine, get_db, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CMS Backend",
    swagger_ui_parameters={
        "syntaxHighlight": False,               # Disable syntax highlighting
        "syntaxHighlight.theme": "obsidian"     # Change theme to "obsidian"
    }
)


# In-memory store for recently viewed articles per user
recently_viewed = {}

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to CMS Backend"}

# Create Article
@app.post("/articles/", response_model=schemas.Article, tags=["Articles"])
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    db_article = models.Article(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

# Get Article by ID and update recently viewed (user_id optional)
@app.get("/articles/{article_id}", response_model=schemas.Article, tags=["Articles"])
def get_article(
    article_id: int,
    user_id: Optional[int] = Query(None, description="ID of the user viewing the article"),
    db: Session = Depends(get_db)
):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Track recently viewed articles if user_id is provided
    if user_id is not None:
        user_views = recently_viewed.setdefault(user_id, [])
        if article_id in user_views:
            user_views.remove(article_id)
        user_views.insert(0, article_id)  # Most recent first
        if len(user_views) > 5:  # Keep only last 5
            user_views.pop()

    return article

# List Articles with pagination
@app.get("/articles/", response_model=List[schemas.Article], tags=["Articles"])
def list_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    articles = db.query(models.Article).offset(skip).limit(limit).all()
    return articles

# Update Article
@app.put("/articles/{article_id}", response_model=schemas.Article, tags=["Articles"])
def update_article(article_id: int, article_update: schemas.ArticleUpdate, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = article_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
    db.commit()
    db.refresh(article)
    return article

# Delete Article
@app.delete("/articles/{article_id}", tags=["Articles"])
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"detail": "Article deleted successfully"}

# Get recently viewed articles for a user
@app.get("/users/{user_id}/recently-viewed", response_model=List[schemas.Article], tags=["Users"])
def get_recently_viewed(user_id: int, db: Session = Depends(get_db)):
    article_ids = recently_viewed.get(user_id, [])
    articles = db.query(models.Article).filter(models.Article.id.in_(article_ids)).all()
    # Sort articles in the order they were viewed
    articles_sorted = sorted(articles, key=lambda x: article_ids.index(x.id))
    return articles_sorted

