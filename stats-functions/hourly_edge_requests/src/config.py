
from arxiv_functions.config import DatabaseConfig, FunctionConfig
from pydantic import Field


class Config(FunctionConfig):
    db: DatabaseConfig | None = None

    max_event_age_in_minutes: int = 50
    fastly_service_id: dict = Field(
        default_factory=lambda: {"arxiv.org": "umpGzwE2hXfa2aRXsOQXZ4"}
    )
    fastly_node_number: int = 0  # existing convention, corresponds to 'fastly'
    hour_delay: int = 1

    fastly_api_token: str


class TestConfig(Config):
    log_locally: bool = True

    fastly_api_token: str = "mock_token"


class DevConfig(Config):
    pass

class ProdConfig(Config):
    pass


config_map = {
    "TEST": TestConfig,
    "DEV": DevConfig,
    "PROD": ProdConfig,
}


def get_config(environment: str) -> Config:
    return config_map[environment]()
