import os
import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.report import MedicalReport
from app.models.biomarker import Biomarker
from app.models.report_analysis import ReportAnalysis
from app.core.config import settings
from app.core.storage import storage_adapter
from app.core.audit import record_audit_log
from app.ml.document_parser import extract_text_and_tables_from_file
from app.ml.lab_extractor import extract_biomarkers_from_text
from app.ml.explainer_ai import generate_plain_explanation

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

def validate_magic_bytes(content: bytes, ext: str) -> bool:
    """Validates file magic header bytes to prevent disguised executable uploads."""
    if ext == ".pdf":
        return content.startswith(b"%PDF-") or b"%PDF-" in content[:1024]
    elif ext == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    elif ext in [".jpg", ".jpeg"]:
        return content.startswith(b"\xff\xd8\xff")
    return False

async def save_uploaded_report(db: AsyncSession, user_id: str, file: UploadFile) -> MedicalReport:
    """Validates, stores, and registers a medical report upload."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, PNG, JPG."
        )

    # Read content into memory for validation
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Validate actual file bytes
    if not validate_magic_bytes(content, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the declared file format signature."
        )

    # Generate isolated random filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    saved_path = await storage_adapter.save_file(content, unique_filename)

    report = MedicalReport(
        user_id=user_id,
        file_path=saved_path,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
        report_type="Blood / Diagnostic Report",
        status="PENDING"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    await record_audit_log(
        db, action="UPLOAD_REPORT", resource_type="MedicalReport",
        resource_id=report.id, actor_user_id=user_id
    )
    return report

async def analyze_report(db: AsyncSession, user_id: str, report_id: str) -> MedicalReport:
    """Orchestrates multi-tier parsing, biomarker extraction, range evaluation, and plain explanation."""
    query = select(MedicalReport).where(
        MedicalReport.id == report_id,
        MedicalReport.user_id == user_id
    ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
    
    result = await db.execute(query)
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    report.status = "ANALYZING"
    await db.commit()

    try:
        # Step 1: Ingest document and extract text & table structures
        extracted_doc = extract_text_and_tables_from_file(report.file_path)
        raw_text = extracted_doc.get("raw_text", "")
        tables = extracted_doc.get("tables", [])

        # Step 2: Extract normalized biomarkers & evaluate flags
        extracted_biomarkers = extract_biomarkers_from_text(raw_text, tables)

        # Clear existing biomarkers if re-analyzing
        for b in report.biomarkers:
            await db.delete(b)
        await db.commit()

        # Save extracted biomarker records
        saved_biomarkers = []
        for b_data in extracted_biomarkers:
            biomarker = Biomarker(
                report_id=report.id,
                test_name=b_data["test_name"],
                canonical_name=b_data["canonical_name"],
                value_numeric=b_data.get("value_numeric"),
                value_text=b_data.get("value_text"),
                unit=b_data.get("unit"),
                reference_min=b_data.get("reference_min"),
                reference_max=b_data.get("reference_max"),
                reference_text=b_data.get("reference_text"),
                flag=b_data.get("flag", "NORMAL"),
                category=b_data.get("category", "General Panel")
            )
            db.add(biomarker)
            saved_biomarkers.append(b_data)

        await db.commit()

        # Step 3: Generate layperson summary and terminology glossary
        explanation_data = generate_plain_explanation(saved_biomarkers, report.report_type)

        # Update or create ReportAnalysis record
        glossary_payload = explanation_data.get("terminology_glossary", [])
        if isinstance(glossary_payload, dict):
            glossary_payload = [{"term": k, "definition": v} for k, v in glossary_payload.items()]
        if report.analysis:
            report.analysis.plain_summary = explanation_data.get("plain_summary", "")
            report.analysis.terminology_glossary = glossary_payload

            report.analysis.clinical_disclaimer = explanation_data.get("clinical_disclaimer", "")
            report.analysis.generated_at = datetime.now(timezone.utc)
        else:
            analysis = ReportAnalysis(
                report_id=report.id,
                plain_summary=explanation_data.get("plain_summary", ""),
                terminology_glossary=glossary_payload,
                clinical_disclaimer=explanation_data.get("clinical_disclaimer", "")
            )
            db.add(analysis)


        # Generate & Persist Report Embedding chunk for multi-report RAG
        from app.models.report_embedding import ReportEmbedding
        from app.core.llm_provider import get_active_llm_provider
        
        bm_summary_parts = [f"{b.get('test_name', '')}: {b.get('value_numeric') if b.get('value_numeric') is not None else b.get('value_text', '')} {b.get('unit') or ''} (Flag: {b.get('flag', 'NORMAL')})" for b in saved_biomarkers]
        chunk_text = f"Report Date: {report.report_date}. Type: {report.report_type}. Biomarkers: {', '.join(bm_summary_parts)}. Summary: {explanation_data.get('plain_summary', '')}"
        
        provider = get_active_llm_provider()
        emb_vector = await provider.generate_embedding(chunk_text)
        
        report_emb = ReportEmbedding(
            report_id=report.id,
            user_id=user_id,
            chunk_type="BIOMARKERS_SUMMARY",
            content_chunk=chunk_text,
            embedding_json=emb_vector,
            metadata_json={
                "report_date": str(report.report_date),
                "report_type": report.report_type,
                "biomarkers_count": len(saved_biomarkers)
            }
        )
        db.add(report_emb)

        report.status = "COMPLETED"
        await db.commit()
        await db.refresh(report)

        await record_audit_log(
            db, action="ANALYZE_REPORT", resource_type="MedicalReport",
            resource_id=report.id, actor_user_id=user_id,
            metadata={"biomarkers_count": len(saved_biomarkers)}
        )

        # Trigger notification (consent-gated)
        from app.models.user import User
        from app.core.notifications import notification_service
        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalars().first()
        if user_obj:
            await notification_service.notify_report_analyzed(
                db=db,
                user=user_obj,
                report_filename=report.file_name
            )

        return await get_report_detail(db, user_id, report_id)

    except Exception as e:
        report.status = "FAILED"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report analysis failed: {str(e)}"
        )

async def list_user_reports(db: AsyncSession, user_id: str) -> List[MedicalReport]:
    """Retrieves all uploaded reports for a user."""
    query = select(MedicalReport).where(
        MedicalReport.user_id == user_id
    ).options(selectinload(MedicalReport.biomarkers)).order_by(MedicalReport.report_date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_report_detail(db: AsyncSession, user_id: str, report_id: str) -> MedicalReport:
    """Retrieves full details of a specific report including biomarkers and layperson explanation."""
    query = select(MedicalReport).where(
        MedicalReport.id == report_id,
        MedicalReport.user_id == user_id
    ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
    
    result = await db.execute(query)
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report

async def delete_report(db: AsyncSession, user_id: str, report_id: str) -> bool:
    """Deletes a report, its files, and all associated extracted records."""
    report = await get_report_detail(db, user_id, report_id)
    await storage_adapter.delete_file(report.file_path)
    await db.delete(report)
    await db.commit()
    await record_audit_log(
        db, action="DELETE_REPORT", resource_type="MedicalReport",
        resource_id=report_id, actor_user_id=user_id
    )
    return True
