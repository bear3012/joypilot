from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, CONTRACT_VERSION, FREE_RELATIONSHIP_DAILY_LIMIT, FREE_REPLY_AD_BONUS, FREE_REPLY_DAILY_LIMIT
from pydantic import BaseModel, Field as PydanticField

from app.contracts import (
    GateDecision,
    PreparedUpload,
    RelationshipAnalyzeRequest,
    ReplyAnalyzeRequest,
    SafetyStatus,
    UploadPrepareRequest,
)
from app.entitlement_service import build_usage_snapshot
from app.input_service import prepare_upload
from app.relationship_service import analyze_relationship
from app.reply_service import analyze_reply
from app.storage import STORE


class ReplyFeedbackRequest(BaseModel):
    user_id: str
    selected_text: str
    rejected_texts: list[str] = PydanticField(default_factory=list)
    context_fingerprint: str
    j28_trend: str | None = None
    j29_naked_punct: bool = False
    j30_triggered: bool = False

app = FastAPI(title=APP_NAME, version=CONTRACT_VERSION)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": APP_NAME,
        "contract_version": CONTRACT_VERSION,
        "reply_free_limit": FREE_REPLY_DAILY_LIMIT,
        "reply_ad_bonus": FREE_REPLY_AD_BONUS,
        "relationship_free_limit": FREE_RELATIONSHIP_DAILY_LIMIT,
    }


@app.post("/upload/prepare", response_model=PreparedUpload)
def upload_prepare(request: UploadPrepareRequest) -> PreparedUpload:
    return prepare_upload(request)


@app.post("/reply/analyze")
async def reply_analyze(request: ReplyAnalyzeRequest):
    response = await analyze_reply(request)
    if response.safety.status.value == "BLOCKED":
        response.dashboard.message_bank = []
    return response


@app.post("/relationship/analyze")
async def relationship_analyze(request: RelationshipAnalyzeRequest):
    response = await analyze_relationship(request)
    if response.gate_decision == GateDecision.BLOCK:
        response.dashboard.message_bank = []
        response.safety.status = SafetyStatus.BLOCKED
        if response.gating_issues:
            response.safety.block_reason = response.gating_issues[0].code
    return response


@app.post("/reply/feedback")
def reply_feedback(request: ReplyFeedbackRequest) -> dict:
    """记录用户对话术的选择，写入复盘库供 Few-Shot 个性化。"""
    from app.contracts import LLMContext
    from app.review_library import add_entry

    llm_ctx = LLMContext(
        j28_trend=request.j28_trend,
        j29_naked_punct=request.j29_naked_punct,
        j30_triggered=request.j30_triggered,
    )
    add_entry(
        user_id=request.user_id,
        selected_text=request.selected_text,
        rejected_texts=request.rejected_texts,
        context_fingerprint=request.context_fingerprint,
        llm_context=llm_ctx,
    )
    return {"status": "ok"}


@app.get("/entitlement/state/{user_id}")
def entitlement_state(user_id: str) -> dict:
    return build_usage_snapshot(user_id)


@app.get("/api/state")
def api_state() -> dict:
    return {
        "reply_sessions": len(STORE.reply_sessions),
        "audit_entries": len(STORE.audit_entries),
        "segment_summaries": len(STORE.segment_summaries),
        "entitlement_states": len(STORE.entitlement_state_by_user_day),
        "entitlement_pending_locks": len(STORE.entitlement_pending_deducts),
    }
