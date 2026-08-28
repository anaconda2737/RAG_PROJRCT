from langchain_core.messages import AnyMessage
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langgraph.graph.message import add_messages
from  .modesl import GradingResult, GuardRailScoring, RoutingDecision, SourceItem, ToolArtiFact


class  AgentState(TypedDict):
    """
    State class  for the agentic RAG workflow 

    """

    messages : Annotated[list[AnyMessage], add_messages]
    original_query: Optional[str]
    rewritten_query: Optional[str]
    retrieval_attempts:int
    guardrail_result: Optional[GuardRailScoring]
    routing_decision: Optional[RoutingDecision]
    sources: Optional[Dict[str,Any]]
    relevant_sources: List[SourceItem]
    relevant_tool_artifacts: Optional[List[ToolArtiFact]]
    grading_result: List[GradingResult]
    metadta: Dict[str, Any]
