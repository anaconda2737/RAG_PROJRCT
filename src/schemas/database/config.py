from pydantic import Field
from pydantic_settings import BaseSettings

class PostgreSQLSettings(BaseSettings):
    database_url:str = Field(
        default = " I will create this later", description="Postgresql database URL"
        
    )
    echo_sql:bool = Field(default=False, description = "Enable SQL query logging")
    pool_size:int = Field(default =  10, description = "Database connection pool size")
    max_overflow:int =  Field(default =  0 , description="Maximum Pool Overflow")

    class Config:
        env_prefix = "POSTGRES_"
        
