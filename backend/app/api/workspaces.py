from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import WorkspaceCreate, WorkspaceRead
from app.database import get_session
from app.models import Workspace

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate, session: SessionDependency
) -> Workspace:
    workspace = Workspace(name=data.name.strip())
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return workspace
