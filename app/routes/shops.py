"""Public lookup of a shop by its slug, so the customer sign-up page can show which shop the
link is for before anyone types anything. Nothing here lists shops or reveals more than a name."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ShopOut
from app.shops import find_shop_by_slug

router = APIRouter(prefix="/api/shops", tags=["shops"])


@router.get("/{slug}", response_model=ShopOut)
def get_shop(slug: str, db: Session = Depends(get_db)):
    shop = find_shop_by_slug(db, slug, active_only=True)
    if shop is None:
        raise HTTPException(status_code=404, detail="That shop doesn't exist.")
    return shop
