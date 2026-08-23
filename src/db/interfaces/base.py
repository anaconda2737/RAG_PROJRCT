from abc import ABC,abstractmethod
from typing import Any,ContextManager,Dict,List,Optional
from sqlalchemy.orm import Session


class BaseDataBase(ABC):
    @abstractmethod
    def startup(self)->None:
        """Initiate the database connection"""

    @abstractmethod
    def teardown(self)->None:
        """Close the db connection """
    @abstractmethod
    def get_session(self)->ContextManager[Session]:
        """Get a database session"""

class BaseRepository(ABC):
    def __init__(self, session:Session):
        self.session = session 
    @abstractmethod
    def create(self,data:Dict[str, any])->Any:
        """Create a new record"""
    @abstractmethod
    def get_by_id(self, record_id:Any)->Any:
        """Get record by id """ 
    @abstractmethod
    def update(self, record_id: Any, data:Dict[str,any])->Optional[Any]:
        """Update record by ID"""
    @abstractmethod
    def delete(self,record_id:Any)->bool:
        """Delete record by Id""" 
    @abstractmethod
    def list(self, limit:int = 100, offset:int = 0)->List[Any]:
        """List records with paginatiom"""
                                


