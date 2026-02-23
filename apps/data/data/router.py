"""API endpoints for the data service."""

import logging
from typing import Annotated

from common.schemas import ResponseModel
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from data.config import settings
from data.database import get_db
from data.schemas import DailyDataSchema, UploadAccepted, UploadStatusSchema
from data.service import DataService

logger = logging.getLogger(__name__)

data_router = APIRouter()


def get_data_service(session: Session = Depends(get_db)) -> DataService:
    return DataService(session)


# ── Upload endpoints ─────────────────────────────────────────────────────────


@data_router.post(
    "/upload/vessel/{vessel_id}/standard",
    status_code=202,
    summary="上传标准 CSV 数据",
    description=(
        "接收船舶 CSV 文件，立即返回 202，后台异步执行数据清洗、存储和 CII 计算。"
        "通过 GET /upload/{upload_id}/status 轮询处理状态。"
    ),
    response_model=ResponseModel[UploadAccepted],
)
async def upload_standard_csv(
    vessel_id: Annotated[int, Path(description="船舶 ID")],
    file: Annotated[UploadFile, File(description="CSV 标准数据文件")],
    background_tasks: BackgroundTasks,
    pitch: float = Query(6.058, description="螺旋桨螺距（用于滑失比计算）"),
    vessel_capacity: float | None = Query(
        None, description="CII 计算吨位（载重吨或总吨），不提供则跳过 CII 计算"
    ),
    service: DataService = Depends(get_data_service),
) -> ResponseModel[UploadAccepted]:
    # File size check
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {settings.max_file_size // (1024 * 1024)} MB",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    # Minimal format check
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 CSV 格式文件")

    # Save file to disk
    file_path = DataService.save_upload_file(content, f"vessel_{vessel_id}", settings.upload_dir)

    # Create upload record (status=pending)
    upload = service.create_upload_record(vessel_id, file_path)

    # Hand off to background task
    background_tasks.add_task(
        DataService.process_upload,
        upload.id,
        vessel_id,
        file_path,
        pitch,
        vessel_capacity,
    )

    return ResponseModel(
        data=UploadAccepted(upload_id=upload.id),
        message="上传成功，后台处理中",
    )


@data_router.get(
    "/upload/vessel/{vessel_id}/history",
    summary="获取船舶上传历史",
    description="按创建时间倒序返回该船舶的上传记录列表，支持分页。",
    response_model=ResponseModel[list[UploadStatusSchema]],
)
def get_upload_history(
    vessel_id: Annotated[int, Path(description="船舶 ID")],
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(10, ge=1, le=100, description="每页条数"),
    service: DataService = Depends(get_data_service),
) -> ResponseModel[list[UploadStatusSchema]]:
    records = service.list_upload_history(vessel_id, offset, limit)
    return ResponseModel(
        data=[UploadStatusSchema.model_validate(r) for r in records],
        message="获取成功",
    )


@data_router.get(
    "/upload/{upload_id}/status",
    summary="查询上传处理状态",
    description="返回单条上传记录，status 字段为 pending | processing | done | failed。",
    response_model=ResponseModel[UploadStatusSchema],
)
def get_upload_status(
    upload_id: Annotated[int, Path(description="上传记录 ID")],
    service: DataService = Depends(get_data_service),
) -> ResponseModel[UploadStatusSchema]:
    upload = service.get_upload_status(upload_id)
    return ResponseModel(
        data=UploadStatusSchema.model_validate(upload),
        message="获取成功",
    )


# ── Data query endpoints ─────────────────────────────────────────────────────


@data_router.get(
    "/daily/vessel/{vessel_id}",
    summary="获取日均数据",
    description="返回 DuckDB 中存储的日均聚合数据（含 CII），按日期倒序分页。",
    response_model=ResponseModel[list[DailyDataSchema]],
)
def get_daily_data(
    vessel_id: Annotated[int, Path(description="船舶 ID")],
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(30, ge=1, le=365, description="每页条数"),
) -> ResponseModel[list[DailyDataSchema]]:
    rows = DataService.get_daily_data(vessel_id, offset=offset, limit=limit)
    return ResponseModel(
        data=[DailyDataSchema(**r) for r in rows],
        message="获取成功",
    )
