"""API routes for the meta service."""

from common.schemas import ResponseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from meta.database import get_db
from meta.repository import MetaRepository
from meta.schemas import (
    AttributeMapping,
    AttributeMappings,
    FuelTypeSchema,
    LabelValue,
    ShipTypeSchema,
    TimeZoneSchema,
)
from meta.service import MetaService

router = APIRouter(prefix="/meta", tags=["元数据"])


def get_meta_service(session: Session = Depends(get_db)) -> MetaService:
    return MetaService(MetaRepository(session))


@router.get(
    "/fuel_type",
    summary="获取燃料类型",
    description="返回系统支持的所有燃料类型，包含中英文名称、缩写及碳排放因子（CF）。",
)
def get_fuel_types(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[FuelTypeSchema]]:
    types = service.get_all_fuel_types()
    data = [FuelTypeSchema.model_validate(t) for t in types]
    return ResponseModel(data=data, message="获取燃料类型成功")


@router.get(
    "/ship_type",
    summary="获取船舶类型",
    description="返回 IMO CII 规定的船舶类型列表，包含类型代码及 CII 计算吨位基准（DWT 或 GT）。",
)
def get_ship_types(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[ShipTypeSchema]]:
    types = service.get_all_ship_types()
    data = [ShipTypeSchema.model_validate(t) for t in types]
    return ResponseModel(data=data, message="获取船舶类型成功")


@router.get(
    "/time_zone",
    summary="获取时区",
    description="返回全球 25 个标准时区（UTC-12 至 UTC+12），供航海日志时区选择使用。",
)
def get_time_zones(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[TimeZoneSchema]]:
    types = service.get_all_time_zones()
    data = [TimeZoneSchema.model_validate(t) for t in types]
    return ResponseModel(data=data, message="获取时区成功")


@router.get(
    "/attributes",
    summary="属性",
    description="返回性能分析支持的船舶属性列表（如航速、主机功率、油耗等），每个属性含字段名与中文描述。",
)
def get_attributes(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[AttributeMapping]]:
    return ResponseModel(data=service.get_attributes(), message="获取属性成功")


@router.get(
    "/attribute_mapping",
    summary="属性组合",
    description="返回用于散点图分析的属性对组合（X 轴 / Y 轴），例如对水航速 vs 主机功率。",
)
def get_attribute_mapping(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[AttributeMappings]]:
    return ResponseModel(data=service.get_attribute_mapping(), message="获取属性组合成功")


@router.get(
    "/fuel_type_category",
    summary="燃料类型分类",
    description="返回燃料大类列表（如 hfo、lng、hydrogen），用于前端筛选和分组展示。",
)
def get_fuel_type_category(
    service: MetaService = Depends(get_meta_service),
) -> ResponseModel[list[LabelValue]]:
    return ResponseModel(data=service.get_fuel_type_categories(), message="获取燃料类型成功")
