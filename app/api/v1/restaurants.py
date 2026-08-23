from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Restaurant
from app.db.session import get_db
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse

router = APIRouter(prefix="/api/v1", tags=["restaurants"])


@router.post(
    "/restaurants",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_restaurant(
    req: RestaurantCreate,
    session: AsyncSession = Depends(get_db),
) -> RestaurantResponse:
    """Create a new restaurant."""
    restaurant = Restaurant(name=req.name)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)
    return RestaurantResponse.model_validate(restaurant)


@router.get(
    "/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
)
async def get_restaurant(
    restaurant_id: int,
    session: AsyncSession = Depends(get_db),
) -> RestaurantResponse:
    """Retrieve a restaurant by ID."""
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return RestaurantResponse.model_validate(restaurant)
