class StatsComponent:
    def __init__(self, 
                 level: int = 1, 
                 experience: int = 0, 
                 base_health: int = 100,
                 strength: int = 1,
                 agility: int = 1,
                 vitality: int = 1,
                 intelligence: int = 1,
                 dexterity: int = 1,
                 luck: int = 1
                ):
        self.level = level
        self.experience = experience
        self.base_health = base_health
        
        self.strength = strength
        self.agility = agility
        self.vitality = vitality
        self.intelligence = intelligence
        self.dexterity = dexterity
        self.luck = luck
        
    def get_max_health_for_level(self) -> int:
        level_bonus = self.level * 10
        
        VITALITY_MULTIPLIER = 8
        vitality_bonus = self.vitality * VITALITY_MULTIPLIER
        
        return self.base_health + level_bonus + vitality_bonus

    def get_attack_power(self) -> int:
         return self.strength * 2 
        
    def get_movement_speed(self) -> float:
        return 5.0 + (self.agility * 0.1)