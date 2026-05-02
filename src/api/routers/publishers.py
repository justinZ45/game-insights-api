from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.orm_models import Publisher
from src.models.pydantic_models import PublisherResponse
from src.api.dependencies import get_db

router = APIRouter(prefix="/publishers", tags=["publishers"])

@router.get("/", response_model=list[PublisherResponse])
def get_all_publishers(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_db)
):
    """Returns a list of publishers, by any optionally provided filters."""

    query = select(Publisher).offset(offset).limit(limit)
    return session.execute(query).scalars().all()


@router.get("/{publisher_id}", response_model=PublisherResponse)
def get_publisher(publisher_id: int, session: Session = Depends(get_db)):
    """Returns a single publisher by ID."""

    publisher = session.get(Publisher, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return publisher