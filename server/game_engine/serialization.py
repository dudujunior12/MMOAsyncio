from server.game_engine.components.player_class import ClassComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.network import NetworkComponent
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from shared.constants import PLAYER_ATTRS
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.game_engine.world import World

class PacketBuilder:

    def __init__(self):
        self._serializers = {
            NetworkComponent: self._serialize_network,
            PositionComponent: self._serialize_position,
            StatsComponent: self._serialize_stats,
            HealthComponent: self._serialize_health,
            ClassComponent: self._serialize_class,
        }

    def serialize_entity(self, world: 'World', entity_id: int) -> dict:
            packet_data = {"entity_id": entity_id}

            # Itera sobre os serializers e atualiza o dicionário
            for comp_class, serializer_func in self._serializers.items():
                component = world.get_component(entity_id, comp_class)
                if component:
                    # Adiciona todos os dados serializados
                    packet_data.update(serializer_func(component))
            
            # O NetworkComponent deve ter adicionado 'asset_type'. 
            # Se for um NPC sem NetworkComponent (improvável no seu setup) ou sem username:
            if "asset_type" not in packet_data:
                # Caso de emergência, usa o ID como asset_type
                type_comp = world.get_component(entity_id, TypeComponent)
                entity_type = type_comp.entity_type if type_comp else "UNKNOWN"
                packet_data["asset_type"] = f"{entity_type}_{entity_id}"
                
            # O HealthComponent deve ser incluído se existir (garantido pelo loop acima e pelo _serialize_health)

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