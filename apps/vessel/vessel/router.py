"""API routes for the vessel service."""

from common.schemas import ResponseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from vessel.database import get_db
from vessel.repository import VesselRepository
from vessel.schemas import VesselCreate, VesselSchema, VesselUpdate
from vessel.service import VesselService

vessel_router = APIRouter(prefix="/vessel", tags=["船舶"])


def get_vessel_service(session: Session = Depends(get_db)) -> VesselService:
    return VesselService(VesselRepository(session))


@vessel_router.get("", summary="获取船舶列表")
def get_vessel_list(
    name: str | None = Query(None, description="船名（模糊搜索）"),
    company_id: int | None = Query(None, description="公司ID"),
    offset: int = Query(0, description="偏移量"),
    limit: int = Query(10, description="每页数量"),
    service: VesselService = Depends(get_vessel_service),
) -> ResponseModel[list[VesselSchema]]:
    vessels = service.get_vessel_list(name, company_id, offset, limit)
    return ResponseModel(data=vessels, message="获取船舶列表成功")


@vessel_router.post("", summary="创建船舶")
def create_vessel(
    body: VesselCreate,
    service: VesselService = Depends(get_vessel_service),
) -> ResponseModel[VesselSchema]:
    vessel = service.create_vessel(body)
    return ResponseModel(data=vessel, message="船舶创建成功")


@vessel_router.get("/{vessel_id}", summary="获取船舶详情")
def get_vessel(
    vessel_id: int,
    service: VesselService = Depends(get_vessel_service),
) -> ResponseModel[VesselSchema]:
    vessel = service.get_vessel_by_id(vessel_id)
    return ResponseModel(data=vessel, message="获取船舶信息成功")


@vessel_router.put("/{vessel_id}", summary="更新船舶信息")
def update_vessel(
    vessel_id: int,
    body: VesselUpdate,
    service: VesselService = Depends(get_vessel_service),
) -> ResponseModel[VesselSchema]:
    vessel = service.update_vessel(vessel_id, body)
    return ResponseModel(data=vessel, message="船舶信息更新成功")


@vessel_router.delete("/{vessel_id}", summary="删除船舶")
def delete_vessel(
    vessel_id: int,
    service: VesselService = Depends(get_vessel_service),
) -> ResponseModel[None]:
    service.delete_vessel(vessel_id)
    return ResponseModel(data=None, message="船舶删除成功")
