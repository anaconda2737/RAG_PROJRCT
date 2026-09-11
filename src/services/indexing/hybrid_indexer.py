import logging
from typing import List,Tuple,Dict
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.opensearch.client import OpenSearchClient
from .text_chunker import TextChunker

logger = logging.getLogger(__name__)

class HybridIndexingService:
    def __init__(self,chunker:TextChunker,embeddings_client:JinaEmbeddingsClient,opensearch_client:OpenSearchClient):
        self.chunker = chunker
        self.embeddings_client = embeddings_client
        self.opensearch_client = opensearch_client

        logger.info("Hybrid Indexing Service initialized")

    async def index_paper(self,paper_data:Dict)-> Dict[str,int]:
        arxiv_id = paper_data.get("arxiv_id")
        paper_id = str(paper_data.get("id",""))

        if not arxiv_id:
            logger.error("Paper Missing arxiv_id")
            return {"chunks_created":0,"chunks_indexed":0,"embedding_generated":0,"errors":1}
        try:
            chunks = self.chunker.chunk_paper(
                title = paper_data.get("title",""),
                abstract = paper_data.get("abstract","")
                full_text = paper_data.get("raw_text",paper_data.get("full_text",""))
                arxiv_id = arxiv_id,
                paper_id = paper_id,
                sections = paper_data.get("sections")
            )  