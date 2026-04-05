from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    simulator_model: str = "gpt-4o-mini"
    evaluator_model: str = "gpt-4o"

    backend_url: str = "http://visionarias_brain_dev:8000"
    webhook_secret: str = ""

    max_parallel: int = 5
    request_timeout: int = 60

    db_path: str = "data/simulator.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
