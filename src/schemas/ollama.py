from typing import List,Optional
from pydantic import BaseModel, Field


class RAGResponse(BaseModel):
    answer:str =  Field(description="answer based on paper excerpt")
    sources:List[str] =  Field(deafult_factory=list, description="List of PDF URLS from paper used in the answer")
    confidence:Optional[str] = Field(deafult=None, description = " Confidence level high , low,medium based on the paper excerpt")
    citation:Optional[List[str]] = Field(default=None, description = "specific arXiv Id or paper title refernce in the pdf")
    