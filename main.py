"""AI 教育诊断系统学生端入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.diagnose_service import diagnose
from services.knowledge_service import get_subjects, get_units, init_knowledge_base
from services.question_service import get_or_generate_questions
from services.remediate_service import remediate


class SubmitRequest(BaseModel):
    subject: str
    unit_id: str
    difficulty: str = "mixed"
    answers: list[dict]


class RemediateRequest(BaseModel):
    subject: str
    weak_points: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("AI 教育诊断系统 - 学生端 Web Demo")
    print("=" * 50)
    init_knowledge_base()
    yield


app = FastAPI(title="AI 教育诊断系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/subjects")
async def api_get_subjects():
    return {"subjects": get_subjects()}


@app.get("/api/subjects/{subject_id}/units")
async def api_get_units(subject_id: str):
    units = get_units(subject_id)
    if not units:
        return {"error": f"学科不存在或知识库未加载：{subject_id}", "units": []}
    return {"subject_id": subject_id, "units": units}


@app.get("/api/subjects/{subject_id}/units/{unit_id}/questions")
async def api_get_questions(
    subject_id: str,
    unit_id: str,
    count: int = 20,
    difficulty: str = "mixed",
    regenerate: bool = False,
    x_deepseek_api_key: str | None = Header(default=None),
):
    result = get_or_generate_questions(
        subject_id,
        unit_id,
        count=count,
        difficulty=difficulty,
        regenerate=regenerate,
        api_key=x_deepseek_api_key,
    )
    if "error" in result and not result.get("questions"):
        return result, 400
    return result


@app.post("/api/submit")
async def api_submit(payload: SubmitRequest):
    result = diagnose(payload.subject, payload.unit_id, payload.answers, difficulty=payload.difficulty)
    if "error" in result and result.get("total") == 0:
        return result, 400
    return result


@app.post("/api/remediate")
async def api_remediate(
    payload: RemediateRequest,
    x_deepseek_api_key: str | None = Header(default=None),
):
    result = remediate(payload.subject, payload.weak_points, api_key=x_deepseek_api_key)
    if "error" in result and not result.get("remediations"):
        return result, 400
    return result


app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
