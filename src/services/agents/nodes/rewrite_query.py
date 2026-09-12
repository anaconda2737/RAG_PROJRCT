import logging
import time
from typing import Dict,List
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from pydantic import BaseModel,Field

from ..context import Context
from ..prompts import REWRITE_PROMPTS
from ..state import AgentState

logger = logging.getLogger(__name__)

class QueryRewriteOutput(BaseModel):
    rewritten_query:str = Field(
        description="The improved query optimized for document retrieval"

    )
    reasoning:str = Field(
        description="Brief explanations  of how  the query  was improved"
    )

async def ainvoke_rewrite_query_step(
            state:AgentState,
            runtime:Runtime[Context]
)->Dict[str,str | List]:

    logger.info("NODE: rewrite_query")
    start_time = time.time()

    original_question = state.get("original_query") or state["messages"][0].content
    current_attempt = state.get("retrieval_attempts",0)

    logger.debug(f"Rewrite query using LLM : {original_question[:100]}...")