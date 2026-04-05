from typing import Any

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.application.agents.style_analyzer.graph import onboarding_app
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models import UserModel

logger = structlog.get_logger()
router = APIRouter()


class StyleAnalysisResponse(BaseModel):
    """Response DTO for style analysis endpoint."""

    status: str
    style_profile: dict[str, Any] | None = None
    system_instruction: str | None = None
    simulation_examples: list[Any] | None = None
    cleaned_sample: str = ""

    model_config = ConfigDict(from_attributes=True)


@router.post("/analyze-style", response_model=StyleAnalysisResponse)
async def analyze_style(
    text_input: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes the style of the provided chat history (text or file).
    Runs the 'Ingestion Subgraph' (Janitor -> Psychologist -> Architect -> Simulator).
    """
    user_id = str(current_user.id)
    logger.info("style_analysis_started", user_id=user_id)

    # 1. Extract Raw Input
    raw_input = ""
    if text_input and len(text_input.strip()) > 10:
        raw_input = text_input
    elif file:
        try:
            content = await file.read()
            raw_input = content.decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {e!s}")
    else:
        raise HTTPException(
            status_code=400, detail="Either text_input or file must be provided"
        )

    # 2. Run Onboarding Graph
    try:
        initial_state = {"raw_input": raw_input, "user_id": user_id}
        result = await onboarding_app.ainvoke(initial_state)

        # 3. Check for errors
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        # 4. Save to Database
        # We manually save here to keep the graph pure

        # Update User Model
        stmt = select(UserModel).where(UserModel.id == current_user.id)
        user_orm = db.execute(stmt).scalars().first()
        if not user_orm:
            logger.error("user_not_found_for_update", user_id=user_id)
            # We don't raise error here to return the result anyway, but persistence failed.
        else:
            user_orm.style_profile = result.get("style_profile")
            user_orm.custom_system_instruction = result.get("system_instruction")
            db.commit()
            db.refresh(user_orm)

        cleaned_input = result.get("cleaned_input") or ""
        return StyleAnalysisResponse(
            status="success",
            style_profile=result.get("style_profile"),
            system_instruction=result.get("system_instruction"),
            simulation_examples=result.get("simulation_examples"),
            cleaned_sample=cleaned_input[:500] + "..." if cleaned_input else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("style_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
