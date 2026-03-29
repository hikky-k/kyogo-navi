"""企業管理API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/", response_model=list[CompanyResponse])
def list_companies(
    category: str | None = Query(None, description="カテゴリでフィルタ"),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業一覧取得"""
    query = db.query(Company)
    if category:
        query = query.filter(Company.category == category)
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    return query.order_by(Company.name).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業詳細取得"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")
    return company


@router.post("/", response_model=CompanyResponse, status_code=201)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """企業登録（管理者のみ）"""
    existing = db.query(Company).filter(Company.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="同名の企業が既に登録されています")

    company = Company(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """企業更新（管理者のみ）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """企業削除（管理者のみ）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")
    db.delete(company)
    db.commit()
