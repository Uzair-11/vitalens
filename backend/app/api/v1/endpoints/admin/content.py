from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.content import BiomarkerReference, GlossaryTerm

router = APIRouter()

# In-memory content cache invalidation hooks
def invalidate_biomarker_cache():
    try:
        from app.ml.lab_extractor import invalidate_biomarker_cache as inv
        inv()
    except Exception:
        pass

def invalidate_glossary_cache():
    try:
        from app.ml.explainer_ai import invalidate_glossary_cache as inv
        inv()
    except Exception:
        pass

# Schemas
class BiomarkerReferenceIn(BaseModel):
    test_name: str
    canonical_name: str
    category: str = "General Panel"
    default_unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    description: Optional[str] = None

class BiomarkerReferenceUpdate(BaseModel):
    test_name: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    default_unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    description: Optional[str] = None

class GlossaryTermIn(BaseModel):
    term: str
    definition: str
    reviewed_by: Optional[str] = None

class GlossaryTermUpdate(BaseModel):
    term: Optional[str] = None
    definition: Optional[str] = None
    reviewed_by: Optional[str] = None

# --- Biomarkers Endpoints ---

@router.get("/biomarkers")
async def list_biomarker_references(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by test name or canonical name"),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """Lists clinical biomarker reference thresholds with search and category filters."""
    q = select(BiomarkerReference)
    if category:
        q = q.where(BiomarkerReference.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(BiomarkerReference.test_name.ilike(pattern) | BiomarkerReference.canonical_name.ilike(pattern))

    res = await db.execute(q)
    return res.scalars().all()

@router.post("/biomarkers", status_code=status.HTTP_201_CREATED)
async def create_biomarker_reference(
    data: BiomarkerReferenceIn,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin creates a new biomarker reference range."""
    # Check duplicate
    existing_q = select(BiomarkerReference).where(BiomarkerReference.test_name.ilike(data.test_name))
    existing_res = await db.execute(existing_q)
    if existing_res.scalars().first():
        raise HTTPException(status_code=400, detail=f"Biomarker reference for '{data.test_name}' already exists.")

    ref = BiomarkerReference(**data.model_dump())
    db.add(ref)
    await db.commit()
    await db.refresh(ref)

    invalidate_biomarker_cache()
    await record_audit_log(
        db, action="CREATE_BIOMARKER_REF", resource_type="BiomarkerReference",
        resource_id=ref.id, actor_user_id=current_admin.id, metadata={"canonical_name": ref.canonical_name}
    )
    return ref

@router.patch("/biomarkers/{ref_id}")
async def update_biomarker_reference(
    ref_id: str,
    data: BiomarkerReferenceUpdate,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin modifies an existing biomarker reference range."""
    q = select(BiomarkerReference).where(BiomarkerReference.id == ref_id)
    res = await db.execute(q)
    ref = res.scalars().first()
    if not ref:
        raise HTTPException(status_code=404, detail="Biomarker reference not found.")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(ref, field, val)

    await db.commit()
    await db.refresh(ref)

    invalidate_biomarker_cache()
    await record_audit_log(
        db, action="UPDATE_BIOMARKER_REF", resource_type="BiomarkerReference",
        resource_id=ref.id, actor_user_id=current_admin.id, metadata=update_dict
    )
    return ref

@router.delete("/biomarkers/{ref_id}")
async def delete_biomarker_reference(
    ref_id: str,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin deletes a biomarker reference range."""
    q = select(BiomarkerReference).where(BiomarkerReference.id == ref_id)
    res = await db.execute(q)
    ref = res.scalars().first()
    if not ref:
        raise HTTPException(status_code=404, detail="Biomarker reference not found.")

    await db.delete(ref)
    await db.commit()

    invalidate_biomarker_cache()
    await record_audit_log(
        db, action="DELETE_BIOMARKER_REF", resource_type="BiomarkerReference",
        resource_id=ref_id, actor_user_id=current_admin.id
    )
    return {"status": "DELETED", "id": ref_id}

# --- Glossary Endpoints ---

@router.get("/glossary")
async def list_glossary_terms(
    search: Optional[str] = Query(None, description="Search glossary terms or definitions"),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """Lists layperson glossary terms."""
    q = select(GlossaryTerm)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(GlossaryTerm.term.ilike(pattern) | GlossaryTerm.definition.ilike(pattern))

    res = await db.execute(q)
    return res.scalars().all()

@router.post("/glossary", status_code=status.HTTP_201_CREATED)
async def create_glossary_term(
    data: GlossaryTermIn,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin adds a new glossary term."""
    existing_q = select(GlossaryTerm).where(GlossaryTerm.term.ilike(data.term))
    existing_res = await db.execute(existing_q)
    if existing_res.scalars().first():
        raise HTTPException(status_code=400, detail=f"Glossary term '{data.term}' already exists.")

    term = GlossaryTerm(**data.model_dump())
    db.add(term)
    await db.commit()
    await db.refresh(term)

    invalidate_glossary_cache()
    await record_audit_log(
        db, action="CREATE_GLOSSARY_TERM", resource_type="GlossaryTerm",
        resource_id=term.id, actor_user_id=current_admin.id, metadata={"term": term.term}
    )
    return term

@router.patch("/glossary/{term_id}")
async def update_glossary_term(
    term_id: str,
    data: GlossaryTermUpdate,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin edits an existing glossary term."""
    q = select(GlossaryTerm).where(GlossaryTerm.id == term_id)
    res = await db.execute(q)
    term = res.scalars().first()
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found.")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(term, field, val)

    await db.commit()
    await db.refresh(term)

    invalidate_glossary_cache()
    await record_audit_log(
        db, action="UPDATE_GLOSSARY_TERM", resource_type="GlossaryTerm",
        resource_id=term.id, actor_user_id=current_admin.id, metadata=update_dict
    )
    return term

@router.delete("/glossary/{term_id}")
async def delete_glossary_term(
    term_id: str,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin deletes a glossary term."""
    q = select(GlossaryTerm).where(GlossaryTerm.id == term_id)
    res = await db.execute(q)
    term = res.scalars().first()
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found.")

    await db.delete(term)
    await db.commit()

    invalidate_glossary_cache()
    await record_audit_log(
        db, action="DELETE_GLOSSARY_TERM", resource_type="GlossaryTerm",
        resource_id=term_id, actor_user_id=current_admin.id
    )
    return {"status": "DELETED", "id": term_id}
