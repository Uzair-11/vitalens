from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.report import MedicalReport
from app.models.biomarker import Biomarker

async def get_biomarker_trends(db: AsyncSession, user_id: str, canonical_names: List[str]) -> List[dict]:
    """
    Fetches time-series data for specified canonical biomarkers across all user reports.
    """
    query = select(MedicalReport).where(
        MedicalReport.user_id == user_id,
        MedicalReport.status == "COMPLETED"
    ).options(selectinload(MedicalReport.biomarkers)).order_by(MedicalReport.report_date.asc())
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    trends_map: Dict[str, dict] = {}
    for canonical in canonical_names:
        trends_map[canonical] = {
            "canonical_name": canonical,
            "category": "General Panel",
            "data_points": []
        }
        
    for r in reports:
        date_str = r.report_date.strftime("%b %d, %Y")
        for b in r.biomarkers:
            for canonical in canonical_names:
                if canonical.lower() in b.canonical_name.lower():
                    trends_map[canonical]["category"] = b.category
                    if b.value_numeric is not None:
                        trends_map[canonical]["data_points"].append({
                            "date": date_str,
                            "value": b.value_numeric,
                            "unit": b.unit or "",
                            "flag": b.flag,
                            "reference_min": b.reference_min,
                            "reference_max": b.reference_max,
                            "report_id": r.id
                        })
                    break

    return list(trends_map.values())

async def compare_two_reports(db: AsyncSession, user_id: str, report_id_1: str, report_id_2: str) -> dict:
    """
    Computes side-by-side delta comparison between two reports.
    """
    q1 = select(MedicalReport).where(MedicalReport.id == report_id_1, MedicalReport.user_id == user_id).options(selectinload(MedicalReport.biomarkers))
    q2 = select(MedicalReport).where(MedicalReport.id == report_id_2, MedicalReport.user_id == user_id).options(selectinload(MedicalReport.biomarkers))
    
    r1_res = await db.execute(q1)
    r2_res = await db.execute(q2)
    r1 = r1_res.scalars().first()
    r2 = r2_res.scalars().first()
    
    if not r1 or not r2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both reports not found.")

    r1_map = {b.canonical_name: b for b in r1.biomarkers}
    r2_map = {b.canonical_name: b for b in r2.biomarkers}
    
    all_keys = set(r1_map.keys()).union(set(r2_map.keys()))
    comparison_items = []
    
    for key in sorted(all_keys):
        b1 = r1_map.get(key)
        b2 = r2_map.get(key)
        
        v1 = b1.value_numeric if b1 else None
        f1 = b1.flag if b1 else None
        v2 = b2.value_numeric if b2 else None
        f2 = b2.flag if b2 else None
        unit = (b2.unit if b2 else (b1.unit if b1 else ""))
        test_name = b2.test_name if b2 else (b1.test_name if b1 else key)
        
        delta = None
        status_change = "STABLE"
        if v1 is not None and v2 is not None:
            delta = round(v2 - v1, 2)
            if f1 in ["HIGH", "LOW"] and f2 == "NORMAL":
                status_change = "IMPROVED"
            elif f1 == "NORMAL" and f2 in ["HIGH", "LOW"]:
                status_change = "WORSENED"
            elif delta != 0:
                status_change = "CHANGED"
        elif v1 is None and v2 is not None:
            status_change = "NEW"

        explanation = f"{test_name}: Observed {v1 or 'N/A'} in previous vs {v2 or 'N/A'} in current report."
        
        comparison_items.append({
            "canonical_name": key,
            "test_name": test_name,
            "unit": unit,
            "report_1_value": v1,
            "report_1_flag": f1,
            "report_2_value": v2,
            "report_2_flag": f2,
            "delta": delta,
            "status_change": status_change,
            "explanation": explanation
        })

    return {
        "report_1_id": r1.id,
        "report_1_date": r1.report_date,
        "report_2_id": r2.id,
        "report_2_date": r2.report_date,
        "items": comparison_items,
        "clinical_disclaimer": "Observed biomarker changes reflect point-in-time laboratory readings and must be interpreted by your physician."
    }
