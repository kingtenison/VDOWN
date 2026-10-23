import os
import sys
from fastapi import Request

# Add root directory to sys.path so backend modules are discoverable on Vercel
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app

@app.middleware("http")
async def vercel_path_router_middleware(request: Request, call_next):
    # Restore original path rewritten by Vercel
    orig_path = request.query_params.get("__path")
    if orig_path:
        request.scope["path"] = orig_path
        query_string = request.scope.get("query_string", b"").decode("utf-8")
        clean_params = [p for p in query_string.split("&") if p and not p.startswith("__path=")]
        request.scope["query_string"] = "&".join(clean_params).encode("utf-8")
    
    return await call_next(request)
