from server.game_engine.collision.shapes import BoxCollider, CircleCollider, SpriteCollider
from server.game_engine.components.collision import CollisionComponent
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
            CollisionComponent: self._serialize_collision,
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
            data['movement_speed'] = comp.get_movement_speed()
                
            return data
        
    def _serialize_collision(self, comp: CollisionComponent) -> dict:
        shape = comp.shape
        data = {
            "collider": {
                "offset_x": comp.offset_x,
                "offset_y": comp.offset_y,
                "is_trigger": comp.is_trigger,
                "type": "unknown"
            }
        }

        if shape is None:
            return data

        if isinstance(shape, BoxCollider):
            data["collider"].update({
                "type": "box",
                "width": getattr(shape, 'hw', 0) * 2,
                "height": getattr(shape, 'hh', 0) * 2
            })
        elif isinstance(shape, CircleCollider):
            data["collider"].update({
                "type": "circle",
                "radius": getattr(shape, 'radius', 0)
            })
        elif isinstance(shape, SpriteCollider):
            data["collider"].update({
                "type": "sprite",
                "width": getattr(shape, 'hw', 0) * 2,
                "height": getattr(shape, 'hh', 0) * 2
            })

        return data

packet_builder = PacketBuilder()