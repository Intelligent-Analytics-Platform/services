"""API routes for the analytics service."""

from __future__ import annotations

import logging
from datetime import date
from typing import Annotated

from common.schemas import ResponseModel
from fastapi import APIRouter, Path, Query

from analytics.config import settings
from analytics.schemas import (
    AttributeFrequency,
    AttributeRelation,
    AttributeValue,
    ConsumptionStatistic,
    OptimizationValues,
    TrimDataResponse,
    VesselCiiData,
    VesselDataPerDayAverage,
    VesselStandardDataInfo,
)
from analytics.service import OptimizationService, StatisticService

logger = logging.getLogger(__name__)

analytics_router = APIRouter()

# ── Statistic endpoints ──────────────────────────────────────────────────────

statistic_router = APIRouter(prefix="/statistic", tags=["统计分析"])


@statistic_router.get(
    "/attribute-frequencies",
    summary="获取直方图属性值频次",
    description="返回所选属性在 vessel_standard_data 中的值及频次（用于数据分析与回放页面直方图）。",  # noqa: E501
)
def get_attribute_frequencies(
    attribute_name: Annotated[str, Query(description="属性名称", example="speed_water")],
    vessel_id: Annotated[int, Query(description="船舶ID", example=1)],
    start_date: Annotated[str, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[str, Query(description="结束日期", example="2023-06-30")],
    min_slip_ratio: Annotated[float, Query(description="最小滑失比", example=-20.0)] = -20.0,
    max_slip_ratio: Annotated[float, Query(description="最大滑失比", example=20.0)] = 20.0,
) -> ResponseModel[list[AttributeFrequency]]:
    data = StatisticService.get_attribute_frequencies(
        attribute_name,
        vessel_id,
        date.fromisoformat(start_date),
        date.fromisoformat(end_date),
        min_slip_ratio,
        max_slip_ratio,
    )
    return ResponseModel(data=data, message="获取属性频次成功")


@statistic_router.get(
    "/attribute-values",
    summary="获取散点图属性值（日期维度）",
    description="返回所选属性在 vessel_data_per_day 中各日期对应的值（用于散点图）。",
)
def get_attribute_values(
    attribute_name: Annotated[str, Query(description="属性名称", example="speed_water")],
    vessel_id: Annotated[int, Query(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
    min_slip_ratio: Annotated[float, Query(description="最小滑失比", example=-20.0)] = -20.0,
    max_slip_ratio: Annotated[float, Query(description="最大滑失比", example=20.0)] = 20.0,
) -> ResponseModel[list[AttributeValue]]:
    data = StatisticService.get_attribute_values(
        attribute_name,
        vessel_id,
        start_date,
        end_date,
        min_slip_ratio,
        max_slip_ratio,
    )
    return ResponseModel(data=data, message="获取属性值成功")


@statistic_router.get(
    "/attribute-relation",
    summary="获取属性关系图数据（双属性散点图）",
    description="返回两个属性在 vessel_data_per_day 中的组合值对（用于能效多角度展示）。",
)
def get_attribute_relation(
    attribute_name1: Annotated[str, Query(description="属性名称1", example="speed_water")],
    attribute_name2: Annotated[str, Query(description="属性名称2", example="me_shaft_power")],
    vessel_id: Annotated[int, Query(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
    min_slip_ratio: Annotated[float, Query(description="最小滑失比", example=-20.0)] = -20.0,
    max_slip_ratio: Annotated[float, Query(description="最大滑失比", example=20.0)] = 20.0,
) -> ResponseModel[list[AttributeRelation]]:
    data = StatisticService.get_attribute_relation(
        attribute_name1,
        attribute_name2,
        vessel_id,
        start_date,
        end_date,
        min_slip_ratio,
        max_slip_ratio,
    )
    return ResponseModel(data=data, message="获取属性关系成功")


@statistic_router.get(
    "/vessel/{vessel_id}/cii",
    summary="获取船舶CII数据（含评级）",
    description="返回过去一年内每日 CII 及评级，依赖 vessel / meta 服务获取船型参数。",
)
def get_vessel_cii(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
) -> ResponseModel[list[VesselCiiData]]:
    data = StatisticService.get_vessel_cii(vessel_id)
    return ResponseModel(data=data, message="获取CII数据成功")


@statistic_router.get(
    "/vessel/{vessel_id}/completeness",
    summary="获取船舶数据完整度",
    description="返回过去5年内每月数据记录数，用于评估数据覆盖率。",
)
def get_vessel_completeness(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
) -> ResponseModel[list[tuple[str, int]]]:
    data = StatisticService.get_vessel_completeness(vessel_id)
    return ResponseModel(data=data, message="获取数据完整度成功")


@statistic_router.get(
    "/vessel/{vessel_id}/date-range",
    summary="获取时间范围内船舶标准数据",
    description="从 vessel_standard_data 返回明细记录，支持降采样（sample_interval）减少数据量。",
)
def get_vessel_data_info_by_date_range(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[str, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[str, Query(description="结束日期", example="2023-06-30")],
    sample_interval: Annotated[
        int, Query(description="采样间隔（默认10，设1返回全量）", example=10)
    ] = 10,
) -> ResponseModel[list[VesselStandardDataInfo]]:
    data = StatisticService.get_vessel_data_info_by_date_range(
        vessel_id,
        date.fromisoformat(start_date),
        date.fromisoformat(end_date),
        sample_interval,
    )
    return ResponseModel(data=data, message="获取数据成功")


@statistic_router.get(
    "/consumption/nmile",
    summary="获取每海里燃油消耗统计",
    description="返回指定燃料类型在时间段内各设备的每海里平均油耗（me/dg/blr/total）。",
)
def get_consumption_statistic_nmile(
    fuel_type: Annotated[str, Query(description="燃料类型", example="hfo")],
    vessel_id: Annotated[int, Query(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[ConsumptionStatistic]:
    data = StatisticService.get_consumption_statistic_nmile(
        fuel_type,
        vessel_id,
        start_date,
        end_date,
    )
    return ResponseModel(data=data, message="获取能耗数据成功")


@statistic_router.get(
    "/consumption/total",
    summary="获取总燃油消耗统计",
    description="返回指定燃料类型在时间段内各设备的总消耗量（me/dg/blr/total）。",
)
def get_consumption_statistic_total(
    fuel_type: Annotated[str, Query(description="燃料类型", example="hfo")],
    vessel_id: Annotated[int, Query(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[ConsumptionStatistic]:
    data = StatisticService.get_consumption_statistic_total(
        fuel_type,
        vessel_id,
        start_date,
        end_date,
    )
    return ResponseModel(data=data, message="获取能耗数据成功")


# ── Optimisation endpoints ───────────────────────────────────────────────────

optimization_router = APIRouter(prefix="/optimization", tags=["优化建议"])


@optimization_router.get(
    "/vessel/{vessel_id}/values",
    summary="获取优化建议页面走势图数据",
    description="返回时间段内总吨位、平均对水航速、平均CII及评级。",
)
def get_optimization_values(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[OptimizationValues]:
    data = OptimizationService.get_optimization_values(vessel_id, start_date, end_date)
    return ResponseModel(data=data, message="获取优化数据成功")


@optimization_router.get(
    "/vessel/{vessel_id}/average",
    summary="获取船舶时段平均数据",
    description="返回时间段内平均对水航速和每海里油耗（不指定日期时取最近7天）。",
)
def get_vessel_time_average(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[date | None, Query(description="开始日期")] = None,
    end_date: Annotated[date | None, Query(description="结束日期")] = None,
) -> ResponseModel[VesselDataPerDayAverage]:
    data = StatisticService.get_vessel_average(vessel_id, start_date, end_date)
    return ResponseModel(data=data, message="获取平均数据成功")


@optimization_router.get(
    "/vessel/{vessel_id}/consumption-total",
    summary="获取某时间段总油耗",
)
def get_consumption_total(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    fuel_type: Annotated[str, Query(description="燃料类型", example="hfo")],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[ConsumptionStatistic]:
    data = StatisticService.get_consumption_statistic_total(
        fuel_type,
        vessel_id,
        start_date,
        end_date,
    )
    return ResponseModel(data=data, message="获取能耗数据成功")


@optimization_router.get(
    "/trim-data/{vessel_id}",
    summary="获取船舶吃水差数据",
    description="返回时间段内逐日 trim 值列表及 trim/draft/speed_water/nmile/cii 均值。",
)
def get_trim_data(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[TrimDataResponse]:
    data = OptimizationService.get_trim_data(vessel_id, start_date, end_date)
    return ResponseModel(data=data, message="获取吃水差数据成功")


@optimization_router.get(
    "/optimize-speed/{vessel_id}",
    summary="获取航速优化建议（需ML模型）",
    description=(
        "基于 XGBoost 模型预测不同航速下的油耗和 CII，返回优化建议列表。 "
        "需要 models_dir 目录下存在 ``{vessel_id}_XGBoost_v*_(all|less).pkl``。"
    ),
)
def optimize_speed(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[list[dict]]:
    data = OptimizationService.optimize_ship_speed(
        vessel_id, start_date, end_date, settings.models_dir
    )
    return ResponseModel(data=data, message="获取航速优化建议成功")


@optimization_router.get(
    "/optimize-trim/{vessel_id}",
    summary="获取吃水差优化建议（需ML模型）",
    description=(
        "基于 XGBoost 模型预测不同吃水差下的油耗和 CII，返回优化建议列表。 "
        "需要 models_dir 目录下存在 ``{vessel_id}_trim_*.pkl``。"
    ),
)
def optimize_trim(
    vessel_id: Annotated[int, Path(description="船舶ID", example=1)],
    start_date: Annotated[date, Query(description="开始日期", example="2023-01-01")],
    end_date: Annotated[date, Query(description="结束日期", example="2023-06-30")],
) -> ResponseModel[list[dict]]:
    data = OptimizationService.optimize_ship_trim(
        vessel_id, start_date, end_date, settings.models_dir
    )
    return ResponseModel(data=data, message="获取吃水差优化建议成功")


# ── Mount both routers ───────────────────────────────────────────────────────

analytics_router.include_router(statistic_router)
analytics_router.include_router(optimization_router)
