from pydantic import BaseModel
from typing import List

class GetVinData(BaseModel):
    vin: List[str]
