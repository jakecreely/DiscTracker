from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class CexIdValidator(BaseModel):
    cex_id: str = Field(pattern=r"^[A-Za-z0-9]+$")


class CexApiItemDetail(BaseModel):
    boxId: str = Field(..., pattern=r"^[A-Za-z0-9]+$")
    boxName: str
    sellPrice: Decimal
    exchangePrice: Decimal
    cashPrice: Decimal


class CexApiItemDetailCreateUpdate(BaseModel):
    boxId: str
    boxName: Optional[str] = None
    sellPrice: Optional[Decimal] = None
    exchangePrice: Optional[Decimal] = None
    cashPrice: Optional[Decimal] = None


class ItemData(BaseModel):
    cex_id: str
    title: str
    sell_price: Decimal
    exchange_price: Decimal
    cash_price: Decimal

    @classmethod
    def from_api(cls, api_data: CexApiItemDetail):
        return cls(
            cex_id=api_data.boxId,
            title=api_data.boxName,
            sell_price=api_data.sellPrice,
            exchange_price=api_data.exchangePrice,
            cash_price=api_data.cashPrice,
        )


class ItemDetailUpdate(BaseModel):
    cex_id: str
    title: Optional[str] = None
    sell_price: Optional[Decimal] = None
    exchange_price: Optional[Decimal] = None
    cash_price: Optional[Decimal] = None


class BoxDetailsWrapper(BaseModel):
    boxDetails: List[CexApiItemDetail]

    @field_validator("boxDetails")
    def validate_and_unpack_box_details(cls, value):
        if len(value) != 1:
            raise ValueError(
                f"boxDetails must contain exactly one item, found {len(value)} items."
            )
        else:
            return value[0]  # Returns the single item


class CexApiError(BaseModel):
    code: str
    internal_message: str
    moreInfo: List[str]


class CexItemApiResponseData(BaseModel):
    ack: str  # Acknolwegment/Status
    data: BoxDetailsWrapper
    error: CexApiError


class CexItemApiResponseWrapper(BaseModel):
    response: CexItemApiResponseData


# CEX API Response Structure
# "response": {
#   "ack": "Success",
#   "data": {
#   "boxDetails": [ItemDetail]
# },
#   "error": {
#       "code": "",
#       "internal_message": "",
#       "moreInfo": []
#   }
# }
