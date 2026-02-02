from sqlalchemy import select, func
from fastapi import Depends, Query, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MovieModel
from schemas.movies import MoviePaginationSchema


router = APIRouter()


@router.get("/", response_model=MoviePaginationSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * per_page

    query = select(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Розрахунок загальної кількості для метаданих
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"
    return {
        "movies": movies,
        "total_pages": total_pages,
        "total_items": total_items,
        "prev_page": f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
    }
