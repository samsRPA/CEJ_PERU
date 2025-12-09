from fastapi import status
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from app.dependencies.Dependencies import Dependencies
from app.application.dto.ProceedingsDto import ProceedingsDto

from app.domain.interfaces.IProceedingsCEJPeruService import IProceedingsCEJPeruService



router = APIRouter()

@router.post(
    "/proceedings/queues_cej_peru",
    response_model=ProceedingsDto,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED
)
@inject
async def publishAllProceedings(
        proceedings_cej_peru_service: IProceedingsCEJPeruService = Depends(Provide[Dependencies.proceedings_cej_peru_service])
):
    try:
        raw_proceedings = await proceedings_cej_peru_service.publishProceedings()
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content="✔️ Mensajes enviados a las cola de cej peru")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


