import logging
from typing import List,Dict
from langgraph.runtime import Runtime
from ..context import Context
from ..modesl import GradeDocuments,GradingResult
from ..prompts import GRADE_DOCUMENTS_PROMPTS
from ..state import AgentState
from .utils import get_latest_context,get_latest_query
import time

logger = logging.getLogger(__name__)

async def ainvoke_grade_documents_step(
        state:AgentState,
        runtime:Runtime[Context]
        
)->Dict[str,str | list]:
    logger.info("NODE: grade_documents")
    start_time = time.time()

    question = get_latest_query(state["messages"])
    context = get_latest_context(state["messages"])

    chunks_preview =[]
    if context:
        context_preview = context[:500]+"..." if len(context)>500 else context
        chunks_preview = [{"text_preview":context_preview,"length":len(context)}]

    span = None
    if runtime.context.langfuse_enabled and runtime.context.trace:
        try:
            span = runtime.context.langfuse_tracer.create_span(
                trace = runtime.context.trace,
                name = "document_grading",
                input_data = {
                    "query":question,
                    "context_length":len(context) if context else 0,
                    "has_context": context is not None,
                    "chunks_received":chunks_preview
                },
                metadata = {
                    "node":"grade_documents",
                    "model":runtime.context.model_name

                }
            )

            logger.debug("Created Langfuse span for document grading")
        except Exception as e:
            logger.warning(f"Faild to create span for grade_documents node : {e}")
    if not context:
        logger.warning("No context found, routing to rewrite query")    

        if span:
            execution_time = (time.time()-start_time)*1000
            runtime.context.langfuse_tracer.end_span(
                span,
                output={"routing_decision":"rewrite_query","reason":"no_context"},
                metadat = {"execution_time_ms": execution_time}

            ) 
        return {"routing_decision":"rewrite_query","grading_results":[]}
    logger.debug(f"Grading context of length{len(context)} characters")

    try:
        grading_prompt = GRADE_DOCUMENTS_PROMPTS.format(
            context = context,
            question = question
        )

        llm = runtime.context.ollama_client.get_langchain_model(
            model = runtime.context.model_name,
            temperatur = 0.0
        )
        structured_llm = llm.with_structured_output(GradeDocuments)

        logger.info("Invoking LLM for document ")

        grading_response = await structured_llm.ainvoke(grading_prompt)

        is_relevant = grading_response.binary_score == "yes"
        score = 1.0 if is_relevant else 0.0

        logger.info(f"LLM grading: score{grading_response.binarys_score},reasoning ={grading_response}")

        grading_result = GradingResult(
            document_id="retrieved_docs",
            is_relevant=is_relevant,
            score= score,
            reasoning = grading_response.reasoning
        )
    except Exception as e:
            logger.error(f"LLM grading failed:{e} fall back to heuristic")

            is_relevant = len(context.strip())>50
            grading_result = GradingResult(
                document_id="retrieved_docs",
                is_relevant=is_relevant,
                score = 1.0 if is_relevant else 0.0
                reasoning=f"Fallback heuristic failed: {'Sufficient content' if is_relevant else 'insufficient content'}"

            )   

            route = "generate_answer" if is_relevant else "rewrite_query"
            logger.info(f"Grading reuslt: {'relevant' if is_relevant else 'not_relevant'},routing to :{route}")

            if span:
                execution_time = (time.time()-start_time)*1000
                runtime.context.langfuse_tracer.end_span(
                    span,
                    output={
                        "routing_decision":route,
                        "is_relevant":is_relevant,
                        "score":score,
                        "reasoning":grading_result.reasoning,
                    },
                    metadta={
                        "execution_time_ms":execution_time,
                        "context_length":len(context)
                    }
                ) 

                return {
                    "routing_decision":route,
                    "grading_results":[grading_result]
                }



    
