import logging 
from contextlib import contextmanager
from typing import Generator , Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.db.interfaces.base import BaseDataBase
from src.schemas.database.config import PostgreSQLSettings

logger =  logging.getLogger(__name__)
Base =  declarative_base()


class PostgreSQLDatabase(BaseDataBase):
    def __init__(self,config:PostgreSQLSettings):
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None

    def startup(self)-> None:
        try:
            logger.info(
                f"attempting to connect to the postgrsql at : {self.config.database_url.split('@')[1] if '@' in self.config.database_url else "localhost"}"
            )    

            self.engine =  create_engine(
                self.config.database_url,
                echo =  self.config.echo_sql,
                pool_size =  self.config.pool_size,
                max_overflow =  self.config.max_overflow,
                pool_pre_ping = True

            )
            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit = False)

            assert self.engine is not None
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 "))
                logger.info ("Database connection established successfully")

            inspector =  inspect(self.engine)
            existing_tables = inspector.get_table_names() 

            Base.metadata.create_all(bind=self.engine)

            update_tables = inspector.get_table_names()
            new_tables = set(updated_tables) - set(existing_tables)

            if new_tables:
                logger.info(f"Created new tables: {', '.join(new_tables)}") 
            else:
                logger.info("All tables already exist - no new tables created")

            logger.info("Postgres database initialize successfully")        
            assert self.engine is not None
            logger.info(f"Database :{self.engine.dadtabase_url}")
            logger.info(f"Total tables: {' ,'.join(update_tables) if update_tables else 'None'}")
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize postgresql database: {e}")
            raise

    def teardown(self)->None:
        if self.engine:
            self.engine.dispose()
            logger.info("Postgresql database connection closed")
    @contextmanager
    def get_session(self)-> Generator[Session,None,None]:

        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call starup() first")
        session =  self.session_factory
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()                   

