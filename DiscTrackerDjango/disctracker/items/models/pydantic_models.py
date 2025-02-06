from pydantic import BaseModel

class ItemDetail(BaseModel):
    boxId: str
    boxName: str
    sellPrice: float 
    exchangePrice: float
    cashPrice: float

class CexItemData(BaseModel):
    data: ItemDetail

class CexItemResponse(BaseModel):
    response: CexItemData