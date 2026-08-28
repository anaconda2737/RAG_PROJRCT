from typing import Any, Dict, List, Optional,Literal
from pydantic import BaseModel,Field


class GuardRailScoring(BaseModel):

    score:int = Field(ge=0, le=100,description="Relevance score is betweeen 0 to 100")
    reason:str = Field(description="Brief reason  for the score")

class GradeDocuments(BaseModel):

    binary_score:Literal["Yes", "No"]  =  Field(description="Document relevance Yes or No")
    reasoning:str = Field(default="", description="Explanation for the decision")


class SourceItem(BaseModel):
    arxiv_id: str = Field(description="arxiv Paper ID")
    title:str = Field(description="Paper Title")
    authors:List[str] =  Field(default_factory=list, description="List of author")
    url: str = Field(description="Link to paper")
    relevance_score:float =  Field(default=0.0, description="Relevance score from search")


    def to_dict(self)-> Dict[str,Any]:

        return{
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "url": self.url,
            "relevance_score": self.relevance_score

        }    
class ToolArtiFact(BaseModel):
    tool_name: str = Field(description="Name of the field")
    tool_call_id:str = Field(description="Unique tool call ID")
    content:Any =  Field(description="Tool result content")
    metadata:Dict[str,Any] = Field(default_factory=dict, description="Additional metadata")


class RoutingDecision(BaseModel):

    route: Literal["retrieve","out of scope", "generate answer","rewrite query"] =  Field(description="Next node to route to ")
    reason:str = Field(default="", description="Reason for routing decision")

class GradingResult(BaseModel):
    document_id:str  =  Field(description="Document identifier")
    is_relevant:bool  = Field(description="Relevance Flag")
    score:float =  Field(default=0.0 , description="Relevance score")
    reasoning:str =  Field(deafult="", description="Grading reasoning")


class ReasoningSteps(BaseModel):
    step_name:str = Field(description="Name of the reasoning step")
    description:str =  Field(description="Human- readable description")
    metadata:Dict[str,Any] = Field(default_factory=dict, description="step metadata")
       

