from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.document_service import DocumentService
from app.models.document import DocumentSet, CreateDocumentRequest

router = APIRouter(prefix="/api", tags=["documents"])

def get_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)

@router.post("/documents", response_model=DocumentSet)
def create_documents(req: CreateDocumentRequest,
                     service: DocumentService = Depends(get_service)):
    return service.create_set(req.booking_id, req.user_id, req.tour_id)

@router.get("/documents/{doc_id}", response_model=DocumentSet)
def get_document(doc_id: UUID, service: DocumentService = Depends(get_service)):
    doc = service.get_set(doc_id)
    if not doc:
        raise HTTPException(404, "Document set not found")
    return doc

@router.get("/documents", response_model=list[DocumentSet])
def list_documents(user_id: str, service: DocumentService = Depends(get_service)):
    return service.list_sets(user_id)

@router.post("/documents/{doc_id}:sign", response_model=DocumentSet)
def sign_contract(doc_id: UUID, service: DocumentService = Depends(get_service)):
    try:
        return service.sign_contract(doc_id)
    except KeyError:
        raise HTTPException(404, "Document set not found")
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: UUID, service: DocumentService = Depends(get_service)):
    try:
        service.cancel_set(doc_id)
    except KeyError:
        raise HTTPException(404, "Document set not found")
    return {"status": "canceled"}