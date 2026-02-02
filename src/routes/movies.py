from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.movies import MoviePaginationSchema


router = APIRouter()


@router.get("/{movie_id}/", response_model=MoviePaginationSchema)
async def get_movies(
        movie_id: int, session: AsyncSession = Depends(get_db)
):
    pass


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, session: AsyncSession = Depends(get_db)):
    pass
