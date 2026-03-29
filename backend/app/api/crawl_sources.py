"""クロールソース管理API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.crawl_source import CrawlSource
from app.models.user import User
from app.schemas.crawl_source import CrawlSourceCreate, CrawlSourceResponse, CrawlSourceUpdate
from app.services.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/", response_model=list[CrawlSourceResponse])
def list_crawl_sources(
    company_id: int | None = Query(None, description="企業IDでフィルタ"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """クロールソース一覧取得"""
    query = db.query(CrawlSource)
    if company_id:
        query = query.filter(CrawlSource.company_id == company_id)
    return query.all()


@router.post("/", response_model=CrawlSourceResponse, status_code=201)
def create_crawl_source(
    data: CrawlSourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """クロールソース登録（管理者のみ）"""
    source = CrawlSource(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/{source_id}", response_model=CrawlSourceResponse)
def update_crawl_source(
    source_id: int,
    data: CrawlSourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """クロールソース更新（管理者のみ）"""
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="クロールソースが見つかりません")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_crawl_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """クロールソース削除（管理者のみ）"""
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="クロールソースが見つかりません")
    db.delete(source)
    db.commit()
