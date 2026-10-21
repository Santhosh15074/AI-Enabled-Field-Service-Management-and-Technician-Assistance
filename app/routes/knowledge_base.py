"""Admin management of the troubleshooting knowledge base — see app.ml.troubleshooting, which
matches a complaint's description against these entries by meaning. Editing here takes effect
immediately: troubleshooting's embedding cache is keyed on the entries themselves, so a change
invalidates it automatically rather than needing an explicit cache-clear.

Each shop has its own entries; a new shop starts with none.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import ComplaintCategory, KnowledgeBaseEntry, Role, User
from app.schemas import KnowledgeBaseEntryIn, KnowledgeBaseEntryOut
from app.shops import not_found_outside_shop

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])


def _serialize(entry: KnowledgeBaseEntry, category_name: str) -> KnowledgeBaseEntryOut:
    return KnowledgeBaseEntryOut(
        id=entry.id,
        category_id=entry.category_id,
        category_name=category_name,
        equipment_type=entry.equipment_type,
        issue_pattern=entry.issue_pattern,
        suggested_fix=entry.suggested_fix,
    )


def _category_name(db: Session, category_id: int) -> str:
    category = db.get(ComplaintCategory, category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="Select a valid category.")
    return category.category_name


def _get_entry(db: Session, entry_id: int, user: User) -> KnowledgeBaseEntry:
    entry = db.get(KnowledgeBaseEntry, entry_id)
    detail = "That knowledge-base entry doesn't exist."
    if entry is None:
        raise HTTPException(status_code=404, detail=detail)
    not_found_outside_shop(entry.shop_id, user, detail)
    return entry


@router.get("", response_model=list[KnowledgeBaseEntryOut])
def list_entries(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    rows = db.execute(
        select(KnowledgeBaseEntry, ComplaintCategory.category_name)
        .join(ComplaintCategory, KnowledgeBaseEntry.category_id == ComplaintCategory.id)
        .where(KnowledgeBaseEntry.shop_id == user.shop_id)
        .order_by(ComplaintCategory.category_name, KnowledgeBaseEntry.id)
    ).all()
    return [_serialize(entry, category_name) for entry, category_name in rows]


@router.post("", response_model=KnowledgeBaseEntryOut, status_code=201)
def create_entry(body: KnowledgeBaseEntryIn, user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    category_name = _category_name(db, body.category_id)
    issue_pattern = body.issue_pattern.strip()
    suggested_fix = body.suggested_fix.strip()
    if not issue_pattern or not suggested_fix:
        raise HTTPException(status_code=400, detail="Both the issue and the fix are required.")

    entry = KnowledgeBaseEntry(
        shop_id=user.shop_id,
        category_id=body.category_id,
        equipment_type=(body.equipment_type or "").strip() or None,
        issue_pattern=issue_pattern,
        suggested_fix=suggested_fix,
    )
    db.add(entry)
    db.commit()
    return _serialize(entry, category_name)


@router.patch("/{entry_id}", response_model=KnowledgeBaseEntryOut)
def update_entry(
    entry_id: int, body: KnowledgeBaseEntryIn, user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)
):
    entry = _get_entry(db, entry_id, user)
    category_name = _category_name(db, body.category_id)
    issue_pattern = body.issue_pattern.strip()
    suggested_fix = body.suggested_fix.strip()
    if not issue_pattern or not suggested_fix:
        raise HTTPException(status_code=400, detail="Both the issue and the fix are required.")

    entry.category_id = body.category_id
    entry.equipment_type = (body.equipment_type or "").strip() or None
    entry.issue_pattern = issue_pattern
    entry.suggested_fix = suggested_fix
    db.commit()
    return _serialize(entry, category_name)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    entry = _get_entry(db, entry_id, user)
    db.delete(entry)
    db.commit()
