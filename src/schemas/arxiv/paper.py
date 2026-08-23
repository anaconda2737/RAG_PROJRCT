from datetime import datetime
from typing import List, Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ArxivPaper(BaseModel):
    arxiv_id:str =  Field(...,description = "arXiv paper id")
    title:str =  Field(..., description = "arXiv paper title")
    author:List[str] =  Field(...,description = "arXiv paper authoe")
    abstract:str =  Field(...,description="arXiv paper abstract")
    categories:List[str] =  Field(...,description = "arXiv paper categories")
    published_data:str =  Field(...,description = "arXiv paper published dat")
    pdf_url:str = Field(...,description="URL to PDF")

class PaperBase(BaseModel):
    arxiv_id:str =  Field(...,description = "arXiv paper id")
    title:str =  Field(..., description = "arXiv paper title")
    author:List[str] =  Field(...,description = "arXiv paper authoe")
    abstract:str =  Field(...,description="arXiv paper abstract")
    categories:List[str] =  Field(...,description = "arXiv paper categories")
    published_data:str =  Field(...,description = "arXiv paper published dat")
    pdf_url:str = Field(...,description="URL to PDF")


class PaperCreate(PaperBase):
    raw_text:Optional[str] =  Field(None,description = "Full raw text extracted from PDF")
    sections:Optional [List[Dict[str,Any]]] = Field(None,description = "List of sections with titles and content")
    references:Optional[List[Dict[str,Any]]] = Field(None,description = "List of references")

    parser_used:Optional[str] =  Field(None,description = "Which Parser was used (DOCLING. etc.)")
    parser_metadata:Optional [Dict[str,Any]] =  Field(None, description =" additional parser metadata")
    pdf_processed:Optional[bool] = Field(False, description="Whether PDF was successfully Processed")
    pdf_processing_date:Optional[datetime] =  Field(None, description="When PDF was processed")

class PaperResponse(PaperBase):
    id: UUID

    raw_text:Optional[str] =  Field(None,description = "Full raw text extracted from PDF")
    sections:Optional [List[Dict[str,Any]]] = Field(None,description = "List of sections with titles and content")
    references:Optional[List[Dict[str,Any]]] = Field(None,description = "List of references")

    parser_used: Optional[str] = Field(None, description="Which parser was used")
    parser_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional parser metadata")
    pdf_processed: bool = Field(False, description="Whether PDF was successfully processed")
    pdf_processing_date: Optional[datetime] = Field(None, description="When PDF was processed")


    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaperSearchResponse(BaseModel):
    papers: List[PaperResponse]
    total: int



    
