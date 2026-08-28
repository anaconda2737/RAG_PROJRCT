import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from functools import cached_property
from pathlib import Path 
from typing  import Dict, List, Optional
from urllib.parse import quote, urlencode
import httpx
from src.config import ArxivSettings
from src.exceptions import ArxivAPIException,ArxivAPITimeoutError,ArxivAPIParseError,PDFDownloadException,PDFDownloadTimeoutError,ArxivParseError
from src.schemas.arxiv.paper import ArxivPaper

logger = logging.getLogger(__name__)


class ArxivClient:
    def __init__(self,settings:ArxivSettings):
        self._settings =  settings
        self._last_request_time = Optional[float] = None

    @cached_property
    def pdf_cach_dir(self)->Path:
        cache_dir = Path(self._settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True,exist_ok=True)
        return cache_dir
    @property
    def base_url(self)->str:
        return self._settings.base_url
    
    @property
    def namespaces(self)->dict:
        return self._settings.namespaces

    @property
    def rate_limit_delay(self)->float:
        return self._settings.rate_limit_delay
    @property
    def timeout_seconds(self)->int:
        return self._settings.timeout_seconds
    @property
    def max_results(self)->str:
        return self._settings.max_results
    @property
    def search_category(self)->str:
        return self._settings.search_category

    async def fetch_papers(
            self,
            max_results: Optional[int] = None,
            start:int = 0,
            sort_by:str = "submittedDate",
            sort_order:str = "descending",
            from_date: Optional[str] = None,
            to_date: Optional[str]=None

    )->List[ArxivPaper]:
        if max_results is None:
            max_results =  self.max_results
        search_query = f"cat:{self.search_category}"

        if from_date or to_date:
            date_from = f"{from_date}0000" if from_date else "*"
            date_to =  f"{to_date}2359" if to_date else "*"
            search_query += f"AND submittedDate:[{date_from}+TO+{date_to}]"

        params = {
            "search_query":search_query,
            "start":start,
            "max_results":min(max_results,2000),
            "sortBy": sort_by,
            "sortOrder": sort_order

        }   
        safe = ":+[]" # don't encode : , +,[,] character needed for arxiv query
        url =  f"{self.base_url}?{urlencode(params,quote_via=quote,safe=safe)}"

        try:
            logger.info(f"Fetching {max_results} {self.search_category} paper from arxiv")

            if self._last_request_time is not  None:
                time_since_last =  time.time() - self._last_request_time
                if time_since_last < self.rate_limit_delay:
                    sleep_time =  self.rate_limit_delay -  time_since_last
                    await asyncio.sleep(sleep_time)
            self._last_request_time =  time.time()

            async with  httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response =  await client.get(url)
                    response.raise_for_status()
                    xml_data = response.text
            papers = self._parse_response(xml_data)
            logger.info(f"Fetched{len(papers)} papers")
            return papers
        except httpx.TimeoutException as e :
            logger.error(f"Arxiv API timeout:{e}")
            raise  ArxivAPITimeoutError(f"arXiv API request  timed out: {e}") 
        except httpx.HTTPStatusError as e:
            logger.error(f"Arxiv API http  error:  {e}")
            raise ArxivAPIException(f"arXiv API  returned error {e.response.status_code}:{e}")
        except Exception as e:
            logger.error(f"failed to fetch paper from from arXiv: {e}")
            raise  ArxivAPIException(f"Unexpected error fetching paper from arXiv: {e}")

   
    async def fetch_papers_with_query(
            self,
            search_query:str,
            max_results:Optional[int] =  None,
            start:int = 0,
            sort_by:str = "submittedDate",
            sort_order:str = "descending"
    )->List[ArxivPaper]:
        if max_results is None:
            max_results = self.max_results
        params = {
            "search_query":search_query,
            "start":start,
            "max_results": min(max_results,2000),
            "sortBy":sort_by,
            "sortOrder":sort_order
        }     

        try:
            if self._last_request_time is not None:
                time_since_last =  time.time() - self._last_request_time
                if time_since_last< self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)
                self._last_request_time =  time.time()

                async with  httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    xml_data =   response.text
                papers =  self._parse_response(xml_data)
                logger.info(f"Query returned {len(papers)} Papers")

                return papers
            
        except httpx.TimeoutException as e:
            logger.error(f"arXiv api timeout : {e}")
            raise ArxivAPITimeoutError(f"arxiv api request time out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXIv api  HTTP error : {e}")
            raise ArxivAPIException(f"arxiv API returned error {e.response.status_code}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch papers from arXiv: {e}")
            raise ArxivAPIException(f"Unexpected error  fetching paper  from arxiv : {e}")

    async def fetch_paper_by_id(self,arxiv_id:str)->Optional[ArxivPaper]:
        clean_id =  arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
        params = {"id_list": clean_id, "max_results": 1}

        safe =  ":+[]*"
        url =  f"{self.base_url}?{urlencode(params,quote_via=quote, safe = safe)}"
        try:
            async with httpx.AsyncClient() as client:
                response =  await client.get(url)
                response.raise_for_status()
                xml_data =  response.text

            papers = self._parse_response(xml_data)

            if papers:
                return papers[0]
            else:
                logger.warning(f"Paper  {arxiv_id} not found")
                return None
        except httpx.TimeoutException as e:
            logger.error(f"arXiv API timeout for paper {arxiv_id}: {e}")
            raise ArxivAPITimeoutError(f"Arxiv API request timed out for paper {arxiv_id}:{e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXiv api  http error for paper {arxiv_id}: {e}")
            raise ArxivAPITimeoutError(f"arXiv api returned  error {e.response.status_code} for {arxiv_id}: {e}")
        except Exception as e :
            logger.error(f"Failed to fetch paper{arxiv_id} from arXiv: {e}")


    def _parse_response(self,xml_data:str) ->List[ArxivPaper]:
        try:
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry",self.namespaces)

            papers = []
            for entry in entries:
                paper =  self._parse_single_entry(entry)
                if paper:
                    papers.append(paper)

            return papers
        except ET.ParseError as e:
            logger.error(f"failed to parse arXiv XML response: {e}")
            raise ArxivParseError(f"Failed to parse arXiv  response: {e}")
        except Exception as e:
            logger.error(f"Unexped error parsing  arXiv response: {e}")

    def _parse_single_entry(self,entry:ET.Element)->Optional[ArxivPaper]:
        try:
            arxiv_id =  self._get_arxiv_id(entry)
            if not arxiv_id:
                return None
            title = self._get_text(entry,"atom:title",clean_newline=True)
            authors = self._get_authors(entry)
            abstract = self._get_text(entry,"atom:summary", cleam_newlines= True)
            published =  self._get_text(entry,"atom:published")
            categories =  self._get_categories(entry)
            pdf_url =  self._get_pdf_url(entry)

            return ArxivPaper(
                arxiv_id = arxiv_id,
                title = title,
                authors = authors,
                abstract = abstract,
                published_data=published,
                categories = categories,
                pdf_url = pdf_url


            )
        except Exception as e:
            logger.error(f"Failed to parse  entry:{e}")
            return None

    def _get_text(self, element:ET.Element, path:str, clean_newlines:bool = False)-> str:
        elem  =  element.find(path, self.namespaces)
        if elem is None or elem.text is None:
            return "" 
        text = elem.text.strip()
        return text.replace("\n"," ") if clean_newlines else text

    def _get_arxiv_id(self,entry: ET.Element)-> Optional[str]:
        id_elem =  entry.find("atom:id", self.namespaces)
        if id_elem is None or id_elem.text is None:
            return None
        return id_elem.text.split("/")[-1]

    def _get_authors(self,entry:ET.Element)-> List[str]:
        authors = []
        for author in entry.findall("atom:author",self.namespaces):
            name =  self._get_text(author,"atom:name")
            if name :
                authors.append(name)
        return authors

    def _get_categories(self, entry:ET.Element)-> List[str]:
        categories = []
        for category in entry .findall("atom:category", self.namespaces):
            term  = category.get("term")
            if term:
                categories.append(term)
            return categories
            
    def _get_pdf_url(self,entry: ET.Element)->str:

        for link in entry.findall("atom:link", self.namespaces):
            if link.get("type") == "applicatin /pdf":
                url =  link.get("href", "")

            if url.startswith("http://arxiv.org"):
                url = url.replace("http://arxiv.org/","https://arxiv.org")  
            return url
        return ""
    async def download_pdf(self,paper:ArxivPaper,force_download:bool = False)-> Optional[Path]:
        if not paper.pdf_url:
            logger.error(f"No PDF url  for paper {paper.arxiv_id}")
            return None
        pdf_path =  self._get_pdf_path(paper.arxiv_id)

        if pdf_path.exists() and not  force_download:
            logger.info(f"Using cached PDF:{pdf_path.name}")
            return pdf_path
        if await  self._download_with_retry(paper.pdf_url,pdf_path):
            return pdf_path
        else:
            return None

    def _get_pdf_path(self, arxiv_id:str)->Path:
        safe_filename =  arxiv_id.replace("/","_") + ".pdf"
        return self.pdf_cach_dir / safe_filename

    async def _download_with_retry(self,url:str,path:Path,max_retries:Optional[int]=None)->bool:
        if max_retries is None:
            max_retries =  self._settings.download_max_retries
        logger.info(f"Downloading PDF from {url}")

        await asyncio.sleep(self.rate_limit_delay)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                    async with client.stream("GET",url) as response:
                        response.raise_for_status()
                        with open (path,"wb") as f:
                            async for chunk in  response.aiter_bytes():
                                f.write(chunk)
                logger.info(f"Successfully downloaded  to {path.name}")
                return True
            except httpx.TimeoutException as e:
                if attempt < max_retries -1:
                    wait_time =  self._settings.download_retry_delay_base * (attempt+1)
                    logger.warning(f"PDF downlod timeout( attempt {attempt+1}/{max_retries}): {e}")
                    logger.info(f"Retrying  in {wait_time}s...")
                    await  asyncio.sleep(wait_time)
                else:
                    logger.error(f"PDF download failed after {max_retries} attempts due to timeout:{e}")
                    raise PDFDownloadTimeoutError(f"PDF download  timed out  after {max_retries} attempts : {e}")
            except httpx.HTTPError as e :
                if attempt < max_retries-1:
                    wait_time =  self._settings.download_retry_delay_base * (attempt+1)
                    logger.warning(f"Download failed(attempt{attempt +1 }/{max_retries}):{e}")
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    raise PDFDownloadException(f"PDF download failed after {max_retries} attemps:{e}")
            except Exception as e:
                logger.error(f"Unexpected download error : {e}")
                raise PDFDownloadException(f"Unexpected error during PDF download : {e}")

        if path.exists():
            path.unlink

        return False                                           


                    




            




        
    





                        

    