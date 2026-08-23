from pydantic import BaseModel, ConfigDict


class RestaurantCreate(BaseModel):
    """Request model for creating a restaurant."""

    name: str


class RestaurantResponse(BaseModel):
    """Response model for a restaurant."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
