
from pydantic import BaseModel, ConfigDict


class Pop(BaseModel):
    edge_requests: int

    model_config = ConfigDict(extra="ignore")


class FastlyStatsApiResponse(BaseModel):
    stats: dict[str, Pop]
