import logging
from typing import List
import httpx
from src.schemas.embedding.jina import JinaEmbeddingRequest, JinaEmbeddingResponse

logger =  logging.getLogger(__name__)


class JinaEmbeddingsClient:
    def __init__(self, api_key:str, base_url:str= "https://api.jina.ai/v1"):
        self.api_key =  api_key
        self.base_url =  base_url
        self.headers = {
            "Authorization": f"Bearer{api_key}",
            "Content-Type": "application/json"

        }
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Jina Embedding client initialized")
    async def embed_passages(self, texts:List[str], batch_size:int = 100)-> List[List[float]]:
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i: i+batch_size]

            request_data = JinaEmbeddingRequest(
                model = "jina-embedding-v3", task="retrieval.passage", dimension= 1024, input = batch
            )
