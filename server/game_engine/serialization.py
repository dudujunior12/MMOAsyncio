from server.game_engine.components.player_class import ClassComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.network import NetworkComponent
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.stats import StatsComponent
from shared.constants import PLAYER_ATTRS

class PacketBuilder:

    def __init__(self):
        self._serializers = {
            StatsComponent: self._serialize_stats,
            PositionComponent: self._serialize_position,
            HealthComponent: self._serialize_health,
            ClassComponent: self._serialize_class,
            NetworkComponent: self._serialize_network
        }

    def serialize_entity(self, world, entity_id: int) -> dict:
        packet_data = {"entity_id": entity_id}

        for comp_class, serializer_func in self._serializers.items():
            component = world.get_component(entity_id, comp_class)
            if component:
                packet_data.update(serializer_func(component))

        if "asset_type" not in packet_data:
            packet_data["asset_type"] = f"NPC_{entity_id}"

        return packet_data

    def _serialize_position(self, comp: PositionComponent) -> dict:
        return {
            "x": comp.x,
            "y": comp.y
        }

    def _serialize_health(self, comp: HealthComponent) -> dict:
        return {
            "current_health": comp.current_health,
            "max_health": comp.max_health
        }

    def _serialize_class(self, comp: ClassComponent) -> dict:
        return {
            "class_name": comp.class_name
        }

    def _serialize_network(self, comp: NetworkComponent) -> dict:
        return {
            "asset_type": comp.username
        }

    def _serialize_stats(self, comp: StatsComponent) -> dict:
            data = {
                "level": comp.level,
                "experience": comp.experience,
                "stat_points": comp.stat_points,
                "base_health": comp.base_health,
            }
            
            for attr in PLAYER_ATTRS:

                total_attr_name = f"total_{attr}"

                data[attr] = getattr(comp, total_attr_name, getattr(comp, attr, 0))

                
            return data

packet_builder = PacketBuilder()