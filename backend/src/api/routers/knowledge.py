from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Depends
from typing import List, Optional, Dict
from src.services.knowledge_service import KnowledgeService
import json
from src.api.dependencies import get_tenant_context

router = APIRouter()
kb_service = KnowledgeService()

@router.get("/stats")
async def get_stats(tenant_id: str = Depends(get_tenant_context)):
    return kb_service.get_system_stats()

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    categories: str = Form(...), # Comma separated or JSON string
    strategy: str = Form("Básico (Rápido)"),
    tenant_id: str = Depends(get_tenant_context)
):
    try:
        content = await file.read()
        
        # Handle categories parsing (expecting JSON list string or comma separated)
        try:
            cat_list = json.loads(categories)
            if not isinstance(cat_list, list):
                cat_list = [str(c).strip() for c in categories.split(",")]
        except Exception:
            cat_list = [str(c).strip() for c in categories.split(",")]

        result = kb_service.ingest_file(
            filename=file.filename,
            file_content=content,
            categories=cat_list,
            strategy=strategy
            # on_progress not supported in sync REST endpoint easily
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents(tenant_id: str = Depends(get_tenant_context)):
    return kb_service.list_documents()

@router.delete("/documents/{filename}")
async def delete_document(filename: str, tenant_id: str = Depends(get_tenant_context)):
    success = kb_service.delete_document(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or delete failed")
    return {"status": "deleted", "filename": filename}

@router.patch("/documents/{filename}/category")
async def update_category(filename: str, categories: List[str] = Body(...), tenant_id: str = Depends(get_tenant_context)):
    success = kb_service.update_document_category(filename, categories)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    return {"status": "updated", "filename": filename, "categories": categories}

@router.post("/search")
async def search_knowledge(
    query: str = Body(..., embed=True),
    limit: int = Body(5, embed=True),
    filters: Optional[Dict] = Body(None, embed=True),
    tenant_id: str = Depends(get_tenant_context)
):
    results = kb_service.search(query, filters=filters, limit=limit, return_raw=True)
    return results

@router.get("/categories")
async def get_categories(tenant_id: str = Depends(get_tenant_context)):
    return kb_service.get_valid_categories()
