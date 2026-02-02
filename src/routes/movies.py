from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload


from database.session_postgresql import get_db
from database.models import MovieModel, GenreModel
from schemas.movies import (
    MoviePaginationSchema, MovieDetailSchema,
    MovieCreateSchema, MovieUpdateSchema
)


router = APIRouter()


@router.get("/", response_model=MoviePaginationSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    total_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_result.scalar()

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    total_pages = (total_items + per_page - 1) // per_page

    return {
        "movies": movies,
        "total_items": total_items,
        "total_pages": total_pages,
        "next_page": f"/api/v1/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "prev_page": f"/api/v1/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    }


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=movie_data.country_id
    )

    if movie_data.genre_ids:
        genres = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids)))
        new_movie.genres = list(genres.scalars().all())

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return await get_movie(new_movie.id, db)


@router.patch("/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return await get_movie(movie.id, db)


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None