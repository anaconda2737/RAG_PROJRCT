import logging
from typing import Dict,List,Optional
from langchain_core.messages import AIMessage,HumanMessage,ToolMessage
from ..modesl import ReasoningSteps, SourceItem,ToolArtiFact

logger = logging.getLogger(__name__)

def extract_sources_from_tool_message(messages:List)->List[SourceItem]:
    sources=[]

    for msg in messages:
            if isinstance(msg,ToolMessage) and hasattr(msg,"name"):
                  if msg.name == "retrieve_papers":
                        pass

    return sources

def extract_tool_artifacts(messages:List)->List[ToolArtiFact]:
        artefacts = []

        for msg in messages:
            if isinstance(msg,ToolMessage):
                  artefacts = ToolArtiFact(
                        tool_name = getattr(msg,"name","unknown"),
                        tool_call_id = getattr(msg,"tool_call_id",""),
                        content = msg.content,
                        metadta = {}

                  )
                  artefacts.append(artefacts)
        return artefacts

def create_reasoning_steps(
            step_name:str,
            description:str,
            metadata:Optional[Dict]=None
)->ReasoningSteps:
      return ReasoningSteps(
            step_name = step_name,
            description=description,
            metadata=metadata or {}
      )          

def filter_messages(messages:List)->List[AIMessage | HumanMessage]:
      return [msg for msg in messages if isinstance(msg,(HumanMessage,AIMessage))]

def get_latest_query(messages:List)->str:
      for msg in reversed(messages):
            if isinstance(msg,HumanMessage):
                  return msg.content
            

def get_latest_context(messages:List)->str:
      for msg in reversed(messages):
            if isinstance(msg,ToolMessage):
                  return msg.content if hasattr(msg,"content") else ""

      return ""            
