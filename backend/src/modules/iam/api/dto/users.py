from pydantic import BaseModel

class TenantSchema(BaseModel):
    id: str
    name: str
    slug: str
    role: str
