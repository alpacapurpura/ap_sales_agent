from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.domain.user import User
from src.modules.iam.api.dependencies import get_current_user
from src.modules.onboarding.application.agents.graph import onboarding_app
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/analyze-style")
async def analyze_style(
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Either text_input or file must be provided")

    # 2. Run Onboarding Graph
    try:
        initial_state = {"raw_input": raw_input, "user_id": user_id}
        result = await onboarding_app.ainvoke(initial_state)
        
        # 3. Check for errors
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
            
        # 4. Save to Database
        # We manually save here to keep the graph pure
        # user_repo = UserRepository(db) - REMOVED: Using current_user directly
        
        # Update User Model
        current_user.style_profile = result.get("style_profile")
        current_user.custom_system_instruction = result.get("system_instruction")
        db.commit()
        
        return {
            "status": "success",
            "style_profile": result.get("style_profile"),
            "system_instruction": result.get("system_instruction"),
            "simulation_examples": result.get("simulation_examples"),
            "cleaned_sample": result.get("cleaned_input")[:500] + "..." if result.get("cleaned_input") else ""
        }
        
    except Exception as e:
        logger.error("style_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
