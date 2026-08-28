class RepositoryException(Exception):
    """Base Exception for repository related error"""

class PaperNotFound(RepositoryException):
    """Exception raised when paper data is not found"""

class PaperNotSaved(RepositoryException):
    """Exception raised when paper is not saved"""

class ParsingException(Exception):
    """Base exception for parsing related error"""

class PDFParsingException(ParsingException):
    """Base exception for pdf parsing related issues"""

class PDFValidationError(PDFParsingException):
    """Exception raised when pdf file validation failed"""

class PDFDownloadException(Exception):
    """Base exception for pdf download related error"""
class PDFDownloadTimeoutError(PDFDownloadException):
    """Exception raised when pdf download timeout expire"""
class PDFCacheException(Exception):
    """Exception raised for pdf cache related error"""


# opensearch exception 
class OpenSearchException(Exception):
    """Base exception for opensearch related error"""


# Arxiv API exception

class ArxivAPIException(Exception):
    """Base Exception for arxiv api related errors"""
class ArxivAPITimeoutError(ArxivAPIException):
    """Exception raised when arXiv API request time out"""
class ArxivAPIRateLimitError(ArxivAPIException):
    """Exception raised when ArXiv api rate limit exceed"""

class ArxivAPIParseError(ArxivAPIException):
    """Exception raised when arxiv api response parsing failed"""
    
class ArxivParseError(ArxivAPIException):
    """Exception raised when arXiv API response parsing fails."""    

# Metadata fetching Exception
class MetaDataFetchingException(Exception):
    """Base exception for metadata fetching pipeline error"""
class PipeLineException(MetaDataFetchingException):
    """Exception raised during pipeline execution"""

class LLMEXCeption(Exception):
    """Base Exception for LLM related error"""

class OllamaException(LLMEXCeption):
    """Excepiton raised for ollama service error"""

class OllamaConnectionError(OllamaException):
    """Exception raised when cannot connect to ollama service"""

class OllamaTimeOutError(OllamaException):
    """Exception raised when ollama service time out"""


# General applications Exception 
class ConfigurationError(Exception):
    """Exception is raised when configuration is invalid"""

