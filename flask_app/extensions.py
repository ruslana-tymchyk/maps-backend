from flask_limiter import Limiter
from flask_limiter.util import get_remote_address 
# Configure rate limiting
limiter = Limiter(
    get_remote_address, #set rate limit per user
    default_limits=["50 per day"],
    storage_uri="memory://",
)
