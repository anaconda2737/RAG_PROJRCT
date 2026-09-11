import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional
from langfuse import Langfuse
from src.config import Settings

logger = logging.getLogger(__name__)

class LangFuseTracer:

    def __init__(self,settings:Settings):
        self.settings = settings.langfuse
        self.client:Optional[Langfuse] =  None

        if self.settings.enabled and self.settings.public_key and self.settings.secret_key:
            try:

                self.client =  Langfuse(
                    public_key = self.settings.public_key,
                    secret_key = self.settings.secret_key,
                    host = self.settings.host,
                    flush_at = self.settings.flush_at,
                    flush_interval = self.settings.flush_interval,
                    debug = self.settings.debug

                )
                logger.info(f"Langfuse v3 tracing initialized (host:{self.settings.host})")
            except Exception as e:
                logger.error(f"Failed to initialize Langfuse :{e}")
                self.client = None
        else:
            logger.info("Lnagfuse tracing disabled or missing credentials")

    def get_callback_handler(
            self,
            trace_name:Optional[str]=None,
            user_id:Optional[str] = None,
            session_id:Optional[str]= None,
            metadata:Optional[DIct[str,Any]] = None,
            tags:Optional[list[str]] = None

    ):
        if not self.client:
            return None
        try:

            from langfuse.langchain import CallbackHandler

            handler = CallbackHandler(
                trace_name = trace_name,
                user_id = user_id,
                session_id = session_id,
                metadata = metadata,
                tags = tags
            )   
            return handler
        except Exception as e:
            logger.error(f"Error creating CallbackHandler: {e}")
            return None

    @contextmanager
    def trace_langgraph_agent(
        self,
        name:str,
        user_id:Optional[str]=None,
        session_id:Optional[str]= None,
        metadata:Optional[Dict[str,Any]] = None,
        tags:Optional[list[str]]=None
    ):
        if not self.client:
            yield(None,None)
            return
        handler = self.get_callback_handler(
            trace_name = name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags = tags
        

        )  
        yield(None,handler)

    def submit_feedback(
            self,
            trace_id:str,
            score:float,
            name:str = "user-feedback",
            comment:Optional[str]=None,

    )->bool:
        if not self.client:
            logger.warning("Cannnot submit feedback : Langfuse is diabled")

        try:
            self.client.score(
                trace_id = trace_id,
                name = name,
                value = score,
                comment = comment
            ) 
            logger.info(f"Submitted feedback for trace {trace_id}:score={score}")
            return True
        except Exception as e:
            logger.error(f"Error submittig feedback:{e}")
            return False

    def flush(self):
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Error flushing langfuse:{e}")

    def shutdown(self):
        if self.client:
            try:
                self.client.flush()
                self.client.shutdown()
            except Exception  as e:
                logger.error(f"Error shutting down langfuse:{e}")

    @contextmanager
    def star_generation(
        self,
        name:str,
        model:str,
        input_data:Any,
        metadata:Optional[Dict[str,Any]] = None
    ):
        if not self.client:
            yield None
            return
        try:
            generation = self.client.generation(
                name = name,
                model = model,
                input = input_data,
                metadata = metadata or {}
            ) 
            yield generation
        except Exception as e:
            logger.error(f"Error Creating generation span:{e}")
            yield None
    @contextmanager
    def start_span(
        self,
        name:str,
        input_data:Optional[Any] = None,
        metadata: Optional[Dict[str,Any]]=None
    ):
        if not self.client:
            yield None
            return 
        try:
            span = self.client.span(
                name = name,
                input = input_data,
                metadata = metadata or {}

            )
            yield span
        except Exception as e:
            logger.error(f"Error creating span:{e}")
            yield None

    def update_generation(
            self,
            generation,
            output:Any,
            usage_metadata:Optional[Dict[str,Any]]=None,
            comletion_start_time:Optional[float] = None,


    ):

        if not generation:
            return
        try:
            update_data = {"output":output} 
            if usage_metadata:
                if "prompt_tokens" in usage_metadata:
                    update_data["usage"]={
                        "input":usage_metadata.get("prompts_tokens",0),
                        "output":usage_metadata.get("completion_tokens",0),
                        "total":usage_metadata.get("total_tokens",0)
                      }

                if "latency_ms" in usage_metadata:
                    update_data["metadata"] = update_data.get("metadata",{})
                    update_data["metadata"]["latency_ms"] = usage_metadata["latency_ms"]

            generation.update(**update_data)
            generation.end()
        except Exception as e:
            logger.error(f"Error updating generation:{e}")

    def update_span(
            self,
            span,
            output:Optional[Any]=None,
            metadata: Optional[Dict[str,Any]]=None,
            level:Optional[str]=None,
            status_message:Optional[str]=None,
    ):
        if not span:
            return 
        try:
            update_data = {}
            if output is not None:
                update_data["output"] = output
            if metadata:
                update_data["metadata"]=metadata
            if level:
                update_data["level"] = level
            if status_message:
                update_data["status_message"] = status_message

            if update_data:
                span.update(**update_data)
            span.end()
        except Exception as e:
            logger.error(f"Error updating span :{e}")                                            
                          

