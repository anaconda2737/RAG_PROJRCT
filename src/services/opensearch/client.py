import logging
from typing import Any,Dict,List,Optional
from opensearchpy import OpenSearch
from src.config import Settings

from .index_config_hybrid import ARXIV_PAPERS_CHUNKS_MAPPING,HYBRID_RPF_PIPELINE
from .query_builder import QueryBuilder 

logger = logging.getLogger(__name__)

class OpenSearchClient:

    def __init__(self,host:str,settings:Settings):
        self.host = host 
        self.settings = settings
        self.index_name =  f"{settings.opensearch.index_name}-{settings.opensearch.chunk_index_suffix}"

        self.client = OpenSearch(
            hosts = [host],
            use_ssl = False,
            verify_certs = False,
            ssl_show_warn = False
        )
        logger.info(f"Opensearch client initializec with host : {host}")
    def healt_check(self)->bool:
        try:
            health = self.client.cluster.health()
            return health ["status"] in ["green","yellow"]
        except Exception as  e:
            logger.error(f"Health check failed:{e}")
            return False

    def get_index_status(self)->Dict[str,Any]:
        try:
            if not  self.client.indices.exists(index=self.index_name):
                return {"index_name":self.index_name,"exist":False,"document_count":0}
            stats_response =  self.client.indices.stats(index=self.index_name)
            index_stats =  stats_response["indices"][self.index_name]["total"]

            return {
                "index_name": self.index_name,
                "exists":True,
                "document_count":index_stats["docs"]["count"],
                "deleted_count":index_stats["docs"]["deleted"],
                "size_in_bytes": index_stats["store"]["size_in_bytes"]
            }        
        except Exception as e:
            logger.error(f"Error  getting index stats:{e}")
            return {"index_name":self.index_name,"exists":False,"document_count":0,"error":str(e)}
    def setup_indices(self,force:bool=False)->Dict[str,Any]:

        results = {}
        results["hybrid_index"] = self._create_hybrid_index(force)
        results["rrf_pipeline"] =  self._create_rrf_pipeline(force)
        return results

    def _create_hybrid_index(self,force:bool=False)->bool:
        try:
            if force and self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted existing hybrid index : {self.index_name}")
            if not self.client.indices.exists(index =self.index_name):
                self.client.indices.create(index=self.index_name, body = ARXIV_PAPERS_CHUNKS_MAPPING)
                logger.info(f"Create hybrid index : {self.index_name}")
                return True
            logger.info(f"Hybrid index already exists:{self.index_name}")
            return False
        except Exception as e:
            if "resource_already_exists_exception" in str(e):
                logger.info(f"Hybrid index already exist (created by another worker): {self.index_name}")
                return False
            logger.error(f"Error in creating hybrid index :{e}")
            raise

    def _create_rrf_pipeline(self,force:bool=False)->bool:
        try:
            pipeline_id =  HYBRID_RPF_PIPELINE["id"]

            if force:
                try:
                    self.client.ingest.get_pipeline(id=pipeline_id)
                    self.client.ingest.delete_pipeline(id=pipeline_id)
                    logger.info(f"Deleted existing pipeline: {pipeline_id}")
                except Exception:
                    pass
            try:
                self.client.ingest.get_pipeline(id = pipeline_id)
                logger.info(f"RRF pipeline already exists:{pipeline_id}")
                return False
            except Exception:
                pass
            pipeline_body = {
                "description": HYBRID_RPF_PIPELINE["description"],
                "phase_results_processors": HYBRID_RPF_PIPELINE["phase_results_processor"]
            }

            self.client.transport.perform_request("PUT",f"/_search/pipeline/{pipeline_id}",body = pipeline_body)
            logger.info(f"Created RRF search Pipeline:{pipeline_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating RRF pipeline:{e}")
            raise

    def search_papers(
            self,query:str, size:int = 10, from_:int  =0,categories:Optional[List[str]]=None,latest:bool = True
    )->Dict[str,Any]:
        return self._search_bm25_only(query=query,size =size,from_ = from_,categories=categories,latest =latest)

    def search_chunk_vector(
            self,query_embedding:List[float],size:int = 10, categories:Optional[List[str]] = None
    )->Dict[str,Any]:
        try:

            filter_clause = []
            if categories:
                filter_clause.append({"terms":{"categories":categories}})
            search_body = {
                "size":size,
                "query":{"knn":{"embedding":{"vector":query_embedding,"k":size}}},
                "_source":{"excludes":["embedding"]}
            }    
            if filter_clause:
                search_body["query"] = {"bool":{"must":[search_body["query"]],"filter":filter_clause}}
                response =  self.client.search(index = self.index_name,body = search_body)
                results = {"total":response["hits"]["total"]["value"],"hits":[]}

                for hit in response ["hits"]["hits"]:
                    chunk = hit["_source"]
                    chunk["score"] = hit["_score"]
                    chunk["chunk_id"] = hit["_id"]
                    results["hits"].append(chunk)
                return results 
        except Exception as e :
            logger.error(f"Vector search error:{e}")
            return{"total":0,"hits":[]}

    def search_unified(
            self,
            query:str,
            query_embedding:Optional[List[float]]=None,
            size:int =  10,
            from_:int = 0,
            categories:Optional[List[str]] = None,
            latest:bool = False,
            use_hybrid:bool = True,
            min_score:float = 0.0,
            

    )->Dict[str,Any]:
        try:
            if not query_embedding or not use_hybrid:
                return self._search_bm25_only(query=query,size=size,from_=from_,categories =categories,latest=latest)
            return self._search_hybrid_native(
                query = query, query_embedding = query_embedding, size = size, min_score = min_score,categories=categories

            )   
        except Exception as e:
            logger.error(f"Unified search error:{e}")
            return {"total":0,"hits":[]}

    def _search_bm25_only(
            self,query:str,size:int,from_:int,categories:Optional[List[str]],latest:bool
    )->Dict[str,Any]:
        builder = QueryBuilder(
            query = query,
            size = size,
            categories = categories,
            latest_papers = latest,
            search_chunks = True
    

        )
        search_body = builder.build()
        response =  self.client.search(index = self.index_name,body = search_body)
        results = {"total":response["hits"]["total"]["value"],"hits":[]}

        for hit in response["hits"]["hits"]:
            chunk =  hit["_source"]
            chunk["score"] = hit["_score"]
            chunk["chunk_id"] = hit["highlight"]
        results["hits"].append(chunk)

        logger.info(f"BM25 search for query '{query[:25]}...' returned {results["total"]} results")
        return results


    def _search_hybrid_native(
            self,query:str,query_embedding:List[float],size:int,categories:Optional[List[str]],min_score:float
    )->Dict[str,Any]:
        builder = QueryBuilder(
            query =  query, size = size*2, from_=0,categories=categories,latest_papers = False, search_chunks =True
        )
        bm25_search_body = builder.build()
        bm25_query = bm25_search_body["query"]
        hybrid_query = {"hybrid":{"queries":[bm25_query,{"knn":{"embedding":{"vector":query_embedding,"k":size*2}}}]}}
        search_body = {
            "size":size,
            "query":hybrid_query,
            "_source":bm25_search_body["_source"],
            "highlights":bm25_search_body["highlights"]
        }
        response = self.client.search(
            index = self.index_name, body = search_body, params={"search_pipeline":HYBRID_RRF_PIPELINE["id"]}

        )
        results = {"total":response["hits"]["total"]["value"],"hits":[]}

        for hit in response["hits"]["hits"]:
            chunk =  hit["_source"]
            chunk["score"] = hit["_score"]
            chunk["chunk_id"] = hit["_id"]

            if "highlight" in hit:
                chunk["highlights"] = hit["highlight"]
            results["hits"].append(chunk)

        logger.info(f"Native hybrid  search for '{query[:50]}...' returned {results['total']} result")
        return results  

    def search_chunk_hybrid(
            self,
            query:str,
            query_embedding:List[float],
            size:int=10,
            categories:Optional[List[str]] = None,
            min_score:float = 0.0


    )->Dict[str,Any]:
        return self._search_hybrid_native(
            query = query, query_embedding=query_embedding,size = size,categories=categories,min_score=min_score


        )
    
    def index_chunk(self,chunk_data:Dict[str,Any],embedding:List[float])->bool:

        try:
            chunk_data["embedding"] = embedding
            response = self.client.index(index=self.index_name,body=chunk_data,refresh=True)
            return response["result"] in ["created","updated"]
        except Exception as e:
            logger.error(f"Error indexing chunk:{e}")
            return False

    def bulk_index_chunks(self,chunks:List[Dict[str,Any]])->Dict[str,Any]:

        from opensearchpy import helpers
        try:
            actions =[]
            for chunk  in  chunks:
                chunk_data =  chunk["chunk_data"].copy()
                chunk_data["embedding"] =  chunk["embedding"]


                action = {"_index":self.index_name,"_source":chunk_data}
                actions.append(action)

            success, failed =  helpers.bulk(self.client,actions,refresh = True)
            logger.info(f"Bulk indexed{success} chunks,{len(failed)} failed")
            return {"success":success,"failed":len(failed)}
        except Exception as e:
            logger.error(f"Bulk chunk indexing error:{e}")
            raise
    def delete_paper_chunk(self,arxiv_id:str)->bool:
            


     
        
        
        

      




        
        