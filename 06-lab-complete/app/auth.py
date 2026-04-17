from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Xác thực API Key từ header.
    Nếu không khớp với settings.agent_api_key sẽ trả về 401.
    """
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Include header: X-API-Key: <your-key>",
        )
    return api_key
