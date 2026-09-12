import logging
import time
from typing import List,Dict,Optional,Literal
from langgraph.runtime import Runtime
from ..context import Context
from ..modesl import GuardRailScoring
from ..state import AgentState
from .utils import get_latest_query
from ..prompts import GUARDRAILL_PROMPT

logger = logging.getLogger(__name__)


def continue_after_guardrail(state:AgentState,runtime:Runtime[Context])->Literal["continue","out_of_scope"]:
    guardrail_result = state.get("guardrail_result")

    if not guardrail_result:
        logger.warning(f"No guardrail result found continue to deafult")
        return "continue"

    score = guardrail_result.score
    threshold = runtime.context.guardrail_threshold

    logger.info(f"Guardrail score: {score}, threshold: {threshold}")

    return "continue" if score>=threshold else "out_of_scope" 

async def ainvoke_guardrail_step(state:AgentState,runtime:Runtime[Context])->Dict[str,GuardRailScoring]:
    logger.info("Node: guardrail validation") 

    start_time = time.time()

    query = get_latest_query(state["messages"])
    logger.debug(f"Evaluating query:{query[:100]}")

    span = None
    if runtime.context.langfuse_enabled and runtime.context.trace:
        try:
            span = runtime.context.langfuse_tracer.create_span(
                trace = runtime.context.trace,
                name = "guardrail_validation",
                input_data = {
                    "query":query,
                    "threshold": runtime.context.guardrail_threshold
                },
                metadata={
                    "node":"guardrail",
                    "model": runtime.context.model_name

                }
            )
            logger.debug("Created langfuse span for guardrail validation(v2SDK)")
        except Exception as e:
            logger.warning(f"Failed to create guardrail validation : {e}")   
    try:
        guardrail_prompt = GUARDRAILL_PROMPT.format(question=query)

        llm = runtime.context.ollama_client.get_langchain_model(
            model=  runtime.context.model_name,
            temperature = 0.0

        )   

        structured_llm = llm.with_structured_output(GuardRailScoring)

        logger.info("Invoking guardrail for llm validation")
        response = await structured_llm.ainvoke(guardrail_prompt)

        logger.info(f"Guardrail result score:   {response.score}, Reason: {response.reason}") 

        if span:
            execution_time = (time.time()-start_time)*1000
            runtime.context.langfuse_tracer.end_span(
                span,
                output={
                    "score":response.score,
                    "reason":response.reason,
                    "decision":"continue" if response.score >= runtime.context.guardrail_threshold else "out_of_scope",
                },
                metadata={
                    "execution_time_ms":execution_time,
                    "threshold":runtime.context.guardrail_threshold
                }
            )

    except Exception as e:
        logger.error(f"LLM guardrail validation failed:{e}, falling back to default")

        response = GuardRailScoring(
            score = 50,
            reason= f"LLM validation failed, using conservative default: {str(e)}"
        ) 
        if span:
            execution_time = (time.time()-start_time)*1000
            runtime.context.langfuse_tracer.update_span(
                    span,
                    output={"score":response.score,"reason":response.reason,"error":str(e)},
                    metadata = {"execution_time_ms":execution_time,"fallback":True},
                    level = "WARNING"
                    
            )
            runtime.context.langfuse_tracer.end_span(span)      
    return {"guardrail_result":response}         

