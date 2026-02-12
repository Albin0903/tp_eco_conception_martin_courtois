import math
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import relationship, DeclarativeBase, selectinload


# Configuration bd & ORM (Async)

# Utilisation de asyncpg pour de meilleures performances I/O
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/pokemon")

engine = create_async_engine(DATABASE_URL, echo=False) # suppressions des logs SQL
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


class PokemonColor(Base):
    __tablename__ = "pokemon_colors"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100))

class PokemonShape(Base):
    __tablename__ = "pokemon_shapes"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100))

class Type(Base):
    __tablename__ = "types"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100))
    generation_id = Column(Integer)
    damage_class_id = Column(Integer)

class PokemonSpecies(Base):
    __tablename__ = "pokemon_species"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100), nullable=False)
    generation_id = Column(Integer)
    evolves_from_species_id = Column(Integer)
    evolution_chain_id = Column(Integer)
    color_id = Column(Integer, ForeignKey("pokemon_colors.id"))
    shape_id = Column(Integer, ForeignKey("pokemon_shapes.id"))
    habitat_id = Column(Integer)
    gender_rate = Column(Integer)
    capture_rate = Column(Integer)
    base_happiness = Column(Integer)
    is_baby = Column(Boolean)
    hatch_counter = Column(Integer)
    has_gender_differences = Column(Boolean)
    growth_rate_id = Column(Integer)
    forms_switchable = Column(Boolean)
    order = Column(Integer)
    conquest_order = Column(Integer)

    color = relationship("PokemonColor", lazy="joined")
    shape = relationship("PokemonShape", lazy="joined")

class Pokemon(Base):
    __tablename__ = "pokemon"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100), nullable=False)
    species_id = Column(Integer, ForeignKey("pokemon_species.id"), nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    base_experience = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    is_default = Column(Boolean, nullable=False)

    species = relationship("PokemonSpecies", lazy="joined")

class PokemonType(Base):
    __tablename__ = "pokemon_types"
    id = Column(Integer, primary_key=True, index=True)  # Clé composite simplifiée
    type_id = Column(Integer, ForeignKey("types.id"), nullable=False)
    slot = Column(Integer, nullable=False)


# Schémas Pydantic

class PokemonRequest(BaseModel):
    id: Optional[int] = None
    identifier: str
    generation_id: Optional[int] = None
    evolves_from_species_id: Optional[int] = None
    evolution_chain_id: Optional[int] = None
    color_id: Optional[int] = None
    shape_id: Optional[int] = None
    habitat_id: Optional[int] = None
    gender_rate: Optional[int] = None
    capture_rate: Optional[int] = None
    base_happiness: Optional[int] = None
    is_baby: Optional[bool] = None
    hatch_counter: Optional[int] = None
    has_gender_differences: Optional[bool] = None
    growth_rate_id: Optional[int] = None
    forms_switchable: Optional[bool] = None
    order: Optional[int] = None
    conquest_order: Optional[int] = None
    height: int = 0
    weight: int = 0
    base_experience: int = 0
    is_default: bool = True

class PokemonResponse(BaseModel):
    id: int
    identifier: str
    generation_id: Optional[int] = None
    evolves_from_species_id: Optional[int] = None
    evolution_chain_id: Optional[int] = None
    color: Optional[str] = None
    shape_id: Optional[str] = None
    habitat_id: Optional[int] = None
    gender_rate: Optional[int] = None
    capture_rate: Optional[int] = None
    base_happiness: Optional[int] = None
    is_baby: Optional[bool] = None
    hatch_counter: Optional[int] = None
    has_gender_differences: Optional[bool] = None
    growth_rate_id: Optional[int] = None
    forms_switchable: Optional[bool] = None
    order: Optional[int] = None
    conquest_order: Optional[int] = None
    height: int
    weight: int
    base_experience: int
    is_default: bool

    model_config = {"from_attributes": True}

class PaginatedResponse(BaseModel):
    items: list[PokemonResponse]
    total: int
    page: int
    size: int
    pages: int


# Application et logique (Async)

# Optimisation: ORJSONResponse est beaucoup plus rapide que JSONResponse standard
app = FastAPI(title="Pokémon API Rest", default_response_class=ORJSONResponse)

def _pokemon_to_response(pokemon: Pokemon) -> PokemonResponse:
    species = pokemon.species
    return PokemonResponse(
        id=pokemon.id,
        identifier=species.identifier,
        generation_id=species.generation_id,
        evolves_from_species_id=species.evolves_from_species_id,
        evolution_chain_id=species.evolution_chain_id,
        color=species.color.identifier if species.color else None,
        shape_id=species.shape.identifier if species.shape else None,
        habitat_id=species.habitat_id,
        gender_rate=species.gender_rate,
        capture_rate=species.capture_rate,
        base_happiness=species.base_happiness,
        is_baby=species.is_baby,
        hatch_counter=species.hatch_counter,
        has_gender_differences=species.has_gender_differences,
        growth_rate_id=species.growth_rate_id,
        forms_switchable=species.forms_switchable,
        order=species.order,
        conquest_order=species.conquest_order,
        height=pokemon.height,
        weight=pokemon.weight,
        base_experience=pokemon.base_experience,
        is_default=pokemon.is_default,
    )

@app.get("/api/objects", response_model=PaginatedResponse)
async def list_objects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    db: AsyncSession = Depends(get_db),
):
    # Compter le total de manière asynchrone
    total_query = select(func.count()).select_from(Pokemon)
    total = await db.scalar(total_query)
    
    pages = math.ceil(total / size) if total else 0
    
    # Récupérer les items
    query = select(Pokemon).order_by(Pokemon.id).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Transformation synchrone (CPU bound, mais rapide)
    return PaginatedResponse(
        items=[_pokemon_to_response(p) for p in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )

@app.get("/api/objects/{object_id}", response_model=PokemonResponse)
async def get_object(object_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Pokemon).where(Pokemon.id == object_id)
    result = await db.execute(query)
    pokemon = result.scalars().first()
    
    if not pokemon:
        raise HTTPException(status_code=404, detail="Object not found")
    return _pokemon_to_response(pokemon)

@app.post("/api/objects", response_model=PokemonResponse, status_code=201)
async def create_object(data: PokemonRequest, db: AsyncSession = Depends(get_db)):
    # Création de l'espèce
    species = PokemonSpecies(
        identifier=data.identifier,
        generation_id=data.generation_id,
        evolves_from_species_id=data.evolves_from_species_id,
        evolution_chain_id=data.evolution_chain_id,
        color_id=data.color_id,
        shape_id=data.shape_id,
        habitat_id=data.habitat_id,
        gender_rate=data.gender_rate,
        capture_rate=data.capture_rate,
        base_happiness=data.base_happiness,
        is_baby=data.is_baby,
        hatch_counter=data.hatch_counter,
        has_gender_differences=data.has_gender_differences,
        growth_rate_id=data.growth_rate_id,
        forms_switchable=data.forms_switchable,
        order=data.order,
        conquest_order=data.conquest_order,
    )
    db.add(species)
    await db.flush() # Async flush

    # Création du Pokémon
    pokemon = Pokemon(
        identifier=data.identifier,
        species_id=species.id,
        height=data.height,
        weight=data.weight,
        base_experience=data.base_experience,
        order=data.order,
        is_default=data.is_default,
    )
    db.add(pokemon)
    await db.commit() # Async commit
    await db.refresh(pokemon) # Async refresh
    
    # Optimisation: Refaire un select propre pour garantir que tout est chargé comme dans le GET
    query = select(Pokemon).where(Pokemon.id == pokemon.id)
    result = await db.execute(query)
    pokemon_loaded = result.scalars().first()
    
    return _pokemon_to_response(pokemon_loaded)

@app.put("/api/objects/{object_id}", response_model=PokemonResponse)
async def update_object(object_id: int, data: PokemonRequest, db: AsyncSession = Depends(get_db)):
    query = select(Pokemon).where(Pokemon.id == object_id)
    result = await db.execute(query)
    pokemon = result.scalars().first()
    
    if not pokemon:
        raise HTTPException(status_code=404, detail="Object not found")

    species = pokemon.species
    # maj de l'espèce
    for field in [
        "identifier", "generation_id", "evolves_from_species_id", "evolution_chain_id", 
        "color_id", "shape_id", "habitat_id", "gender_rate", "capture_rate", 
        "base_happiness", "is_baby", "hatch_counter", "has_gender_differences", 
        "growth_rate_id", "forms_switchable", "order", "conquest_order"
    ]:
        val = getattr(data, field)
        if val is not None: # maj partielle
            setattr(species, field, val)

    # maj du Pokémon
    pokemon.identifier = data.identifier
    pokemon.height = data.height
    pokemon.weight = data.weight
    pokemon.base_experience = data.base_experience
    pokemon.order = data.order
    pokemon.is_default = data.is_default

    await db.commit()
    # Pas besoin de refresh complet, mais pour la correctness on peut
    # -> retourne l'objet modifié
    return _pokemon_to_response(pokemon)

@app.delete("/api/objects/{object_id}", status_code=204)
async def delete_object(object_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Pokemon).where(Pokemon.id == object_id)
    result = await db.execute(query)
    pokemon = result.scalars().first()
    
    if not pokemon:
        raise HTTPException(status_code=404, detail="Object not found")

    # suppression en cascade manuelle
    await db.execute(delete(PokemonType).where(PokemonType.id == object_id))
    
    db.delete(pokemon)
    await db.commit()

    return None


