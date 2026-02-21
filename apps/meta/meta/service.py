"""Business logic for the meta service."""

from meta.repository import MetaRepository
from meta.schemas import AttributeMapping, AttributeMappings, LabelValue


class MetaService:
    def __init__(self, repository: MetaRepository):
        self.repository = repository

    def get_all_fuel_types(self):
        return self.repository.get_all_fuel_types()

    def get_all_ship_types(self):
        return self.repository.get_all_ship_types()

    def get_all_time_zones(self):
        return self.repository.get_all_time_zones()

    def get_attributes(self) -> list[AttributeMapping]:
        return [
            AttributeMapping(attribute="speed_ground", description="对地航速"),
            AttributeMapping(attribute="speed_water", description="对水航速"),
            AttributeMapping(attribute="draft", description="船艏船尾平均吃水"),
            AttributeMapping(attribute="trim", description="船舶纵倾"),
            AttributeMapping(attribute="me_rpm", description="主机转速"),
            AttributeMapping(attribute="wind_speed", description="风速"),
            AttributeMapping(attribute="wind_direction", description="风向"),
            AttributeMapping(attribute="slip_ratio", description="滑失比"),
            AttributeMapping(attribute="me_fuel_consumption_nmile", description="主机每海里油耗"),
            AttributeMapping(
                attribute="me_fuel_consumption_kwh",
                description="主机每千瓦时油耗（g/kWh）",
            ),
            AttributeMapping(attribute="me_shaft_power", description="主机功率"),
        ]

    def get_attribute_mapping(self) -> list[AttributeMappings]:
        return [
            AttributeMappings(
                attribute_left=AttributeMapping(attribute="speed_water", description="对水航速"),
                attribute_right=AttributeMapping(
                    attribute="me_shaft_power", description="主机功率"
                ),
            ),
            AttributeMappings(
                attribute_left=AttributeMapping(attribute="speed_water", description="对水航速"),
                attribute_right=AttributeMapping(
                    attribute="me_fuel_consumption_nmile",
                    description="主机每海里油耗（Kg/NM）",
                ),
            ),
            AttributeMappings(
                attribute_left=AttributeMapping(attribute="me_rpm", description="主机转速"),
                attribute_right=AttributeMapping(
                    attribute="me_shaft_power", description="主机功率"
                ),
            ),
            AttributeMappings(
                attribute_left=AttributeMapping(attribute="me_rpm", description="主机转速"),
                attribute_right=AttributeMapping(
                    attribute="me_fuel_consumption_kwh",
                    description="主机功率油耗（g/kWh）",
                ),
            ),
            AttributeMappings(
                attribute_left=AttributeMapping(attribute="me_shaft_power", description="主机功率"),
                attribute_right=AttributeMapping(
                    attribute="me_fuel_consumption_kwh",
                    description="主机功率油耗（g/kWh）",
                ),
            ),
        ]

    def get_fuel_type_categories(self) -> list[LabelValue]:
        return [
            LabelValue(value="hfo", label="重油"),
            LabelValue(value="lfo", label="轻油"),
            LabelValue(value="mgo", label="船舶柴油"),
            LabelValue(value="mdo", label="内河船用燃料油"),
            LabelValue(value="lng", label="液化天然气"),
            LabelValue(value="lpg_p", label="液化石油气(丙烷)"),
            LabelValue(value="lpg_b", label="液化石油气(丁烷)"),
            LabelValue(value="methanol", label="甲醇"),
            LabelValue(value="ethanol", label="乙醇"),
            LabelValue(value="ethane", label="乙烷"),
            LabelValue(value="ammonia", label="氨"),
            LabelValue(value="hydrogen", label="氢"),
        ]
