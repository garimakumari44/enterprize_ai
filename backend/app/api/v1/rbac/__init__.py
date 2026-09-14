from fastapi import APIRouter


from .roles import router as roles_router
from .permissions import router as permissions_router
from .policies import router as policies_router



router = APIRouter()


router.include_router(
    roles_router
)


router.include_router(
    permissions_router
)


router.include_router(
    policies_router
)