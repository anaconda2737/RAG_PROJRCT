from typing import Dict, List
from pydantic import BaseModel


class JinaEmbedding(BaseModel):
    model:str = "jina-embedding-v3"
    task:str = "retrieval-passage"
    dimension:int = 1024
    late_chunking:bool =  False
    embedding_type:str = "float"
    input: List[str]

class JinaEmbeddingResponse(BaseModel):
    model:str
    object:str = "list"
    usage:Dict[str,int]
    data:List[Dict]
          
