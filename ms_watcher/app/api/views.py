from fastapi import APIRouter

from app.api.routes import proceeding_cej_peru_routes

apiRouter = APIRouter(prefix="/api/v1")
apiRouter.include_router(proceeding_cej_peru_routes.router, tags=["keys"])

def getApiRouter():
    return apiRouter