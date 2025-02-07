from typing import List
from pydantic import BaseModel, Field

class CexIdValidator(BaseModel):
    cex_id: str = Field(pattern=r'^[A-Za-z0-9]+$')

class ItemDetail(BaseModel):
    boxId: str
    boxName: str
    sellPrice: float 
    exchangePrice: float
    cashPrice: float
        
class CexApiError(BaseModel):
    code: str
    internal_message: str
    moreInfo: List[str]
class CexItemApiResponseData(BaseModel):
    ack: str # Acknolwegment/Status
    data: List[ItemDetail]
    error: CexApiError
    
class CexItemApiResponseWrapper(BaseModel):
    response: CexItemApiResponseData

# CEX API Response Structure
# "response": {
#   "ack": "Success",
#   "data": {},
#   "error": {
#       "code": "",
#       "internal_message": "",
#       "moreInfo": []
#   }
# }