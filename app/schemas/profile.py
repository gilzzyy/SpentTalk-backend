from decimal import Decimal
from pydantic import BaseModel, Field

class ProfileBase(BaseModel):
    saldo_awal: Decimal = Field(default=Decimal("0.0"), ge=0)
    penghasilan_bulanan: Decimal = Field(default=Decimal("0.0"), ge=0)
    budget_makan: Decimal = Field(default=Decimal("0.0"), ge=0)
    budget_transport: Decimal = Field(default=Decimal("0.0"), ge=0)
    budget_jajan: Decimal = Field(default=Decimal("0.0"), ge=0)
    budget_lainnya: Decimal = Field(default=Decimal("0.0"), ge=0)

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
