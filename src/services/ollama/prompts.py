import json
import re
from pathlib import Path    
from typing import List,Dict,Optional,Any
from pydantic import ValidationError
from src.schemas.ollama import RAGResponse


class RAGPrompBuilder:

    def __init__(self):
        self.prompts_dir =  Path(__file__).parent /"prompts"
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self)->str:

        prompt_file =  self.prompts_dir / "rag_system.txt"
        if not prompt_file.exists():
            return(
                "You are an AI assistant specialized in answering question about "
                "acaemic papers from arxiv . Base your answer STRICTLY on the provided"
                "paper excerpt. "
            )
        return prompt_file.read_text().strip()

    def create_rag_prompts(self, query:str,chunks:List[Dict[str,Any]])->str:

        prompts = f"{self.system_prompt}\n\n"
        prompts+="### context from papers:\n\n"

        for i, chunk in enumerate(chunks,1):
            chunk_text = chunk.get("chunk_text",chunk.get("content",""))
            arxiv_id =  chunk.get("arxiv_id","")

            prompts+=f"[{i}. arXiv:{arxiv_id}]\n"
            prompts+=f"{chunk_text}\n\n"

        prompt+=f"### Question:\n{query}\n\n"
        prompt+=(
            "### Answer:\nProvide a natural, conversational response(not JSON) and cite sources using [arXiv:id] format .\n\n"

        ) 
        return prompt

    def create_structured_prompt(self,query:str,chunks:List[Dict[str,Any]])-> Dict[str,Any]:
        prompt_text = self.create_rag_prompts(query,chunks)

        return {
            "prompt":prompt_text,
            "format":RAGResponse.model_json_schema()
        }   

class ResponseParser:
    @staticmethod
    def parse_structured_response(response:str)->Dict[str,Any]:
        try:
            parsed_json =  json.loads(response)
            validated_response =  RAGResponse(**parsed_json)
            return validated_response.model_dump()
        except (json.JSONDecodeError, ValidationError):
            return ResponseParser._extract_json_fallback(response)

    @staticmethod
    def _extract_json_fallback(response:str)->Dict[str,Any]:
        json_match = re.search(r"\{.*\}",response,re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                validated = RAGResponse(**parsed)
                return validated.model_dump()
            except (json.JSONDecodeError, ValidationError):
                pass
        return{
            "answer":response,
            "sources":[],
            "confidence":"low",
            "citations":[]
        }          
