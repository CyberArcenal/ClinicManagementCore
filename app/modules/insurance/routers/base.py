from fastapi import FastAPI


def insurance_router(api_router:FastAPI) -> FastAPI:
    from app.modules.insurance.api.v1.endpoints.insurance_detail import router as insurance_detail_router
    from app.modules.insurance.api.v1.endpoints.insurance_claim import router as insurance_claim_router

    api_router.include_router(insurance_detail_router)
    api_router.include_router(insurance_claim_router)
    
    return api_router