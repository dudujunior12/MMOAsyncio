class World:
    def __init__(self):
        self.next_entity_id = 1
        self.entities = {}  # {entity_id: {ComponentType: ComponentInstance}}
        # Ex: {1: {PositionComponent: PositionComponent(0,0), NetworkComponent: NetworkComponent(writer, username)}}
        
    def create_entity(self):
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        self.entities[entity_id] = {}
        return entity_id

    def add_component(self, entity_id: int, component):
        if entity_id not in self.entities:
            raise ValueError(f"Entity ID {entity_id} does not exist.")
        component_type = type(component)
        self.entities[entity_id][component_type] = component
    
    def get_component(self, entity_id: int, component_type):
        return self.entities.get(entity_id, {}).get(component_type, None)
    
    def remove_entity(self, entity_id: int):
        if entity_id in self.entities:
            del self.entities[entity_id]
            
    def get_entities_with_components(self, component_types: tuple):
        for entity_id, components in self.entities.items():
            if all(comp_type in components for comp_type in component_types):
                yield entity_id, [components[comp_type] for comp_type in component_types]
                
    def get_components_of_type(self, component_type):
        for entity_id, components in self.entities.items():
            if component_type in components:
                component_instance = components[component_type]
                yield entity_id, (component_instance,)