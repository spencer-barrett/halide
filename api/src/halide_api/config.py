from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local")

#    secret_id: str
#    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str
    endpoint_url: str
    database_url: str
    database_url_pooled: str
    database_dev: str
    database_test: str
    auth0_domain: str
    auth0_audience: str
    auth0_algorithms: str

settings = Settings() # type: ignore

