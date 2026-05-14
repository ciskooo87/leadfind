from pydantic import BaseModel, HttpUrl


class CompanyCreate(BaseModel):
    legal_name: str
    trade_name: str | None = None
    cnpj_root: str | None = None
    sector: str | None = None
    city: str | None = None
    state: str | None = None
    estimated_size: str | None = None
    website: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None
    aliases: list[str] = []


class CompanyMatchRequest(BaseModel):
    company_name: str | None = None
    website: HttpUrl | None = None
    city: str | None = None
    state: str | None = None
    cnpj_root: str | None = None


class CompanyRead(BaseModel):
    id: int
    legal_name: str
    trade_name: str | None = None
    cnpj_root: str | None = None
    sector: str | None = None
    city: str | None = None
    state: str | None = None
    estimated_size: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    aliases: list[str] = []

    model_config = {"from_attributes": True}
