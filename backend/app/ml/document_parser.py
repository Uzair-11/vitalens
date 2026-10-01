import os
import io
import re
from typing import List, Dict, Any
from pypdf import PdfReader
import pdfplumber
from app.ml.ocr_engine import process_image_document

def extract_text_and_tables_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extracts text streams and table rows from PDF files with multi-tier fallback
    for scanned, native, or pseudo-PDF test documents.
    """
    extracted_text = []
    extracted_tables = []
    
    # Tier 1: Try pdfplumber (best for tables)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text.append(page_text)
                
                tables = page.extract_tables()
                for table in tables:
                    clean_table = []
                    for row in table:
                        if any(row):
                            clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                            clean_table.append(clean_row)
                    if clean_table:
                        extracted_tables.append(clean_table)
    except Exception:
        pass

    if not extracted_text:
        # Tier 2: Try standard PyPDF Reader
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
        except Exception:
            pass

    if not extracted_text:
        # Tier 3: Try reading as text/UTF-8 directly (e.g. mock/demo/text-based files)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if content and len(content.strip()) > 0:
                    extracted_text.append(content)
                    # Extract table rows if pipe-separated
                    pipe_rows = []
                    for line in content.splitlines():
                        if "|" in line:
                            cols = [c.strip() for c in line.split("|")]
                            pipe_rows.append(cols)
                    if pipe_rows:
                        extracted_tables.append(pipe_rows)
        except Exception:
            pass

    full_text = "\n".join(extracted_text).strip()
    return {
        "raw_text": full_text,
        "tables": extracted_tables,
        "page_count": max(1, len(extracted_text))
    }

import tempfile
import urllib.request
from urllib.parse import urlparse

def extract_text_and_tables_from_file(file_path: str) -> Dict[str, Any]:
    """Unified file parser dispatching to PDF extractor or image OCR extractor based on file extension.
    Supports both local file paths and remote HTTP/HTTPS cloud URLs (e.g. ImageKit, GCS, S3).
    """
    if file_path.startswith(("http://", "https://")):
        parsed_url = urlparse(file_path)
        ext = os.path.splitext(parsed_url.path)[1].lower()
        if not ext:
            ext = ".pdf"
            
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            req = urllib.request.Request(
                file_path,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VitaLens/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as f_out:
                f_out.write(resp.read())

            return _extract_from_local_path(tmp_path, ext)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    else:
        ext = os.path.splitext(file_path)[1].lower()
        return _extract_from_local_path(file_path, ext)

def _extract_from_local_path(local_path: str, ext: str) -> Dict[str, Any]:
    if ext in [".png", ".jpg", ".jpeg"]:
        return process_image_document(local_path)
    return extract_text_and_tables_from_pdf(local_path)

