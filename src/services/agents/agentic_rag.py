import logging
import time
from typing import Dict,List,Optional
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.langfuse.client  import LangFuseTracer
from src.services.opensearch.client import OpenSearchClient
from .config import GraphConfig
from .context import Context
