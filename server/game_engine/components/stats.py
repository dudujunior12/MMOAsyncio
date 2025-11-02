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
        
        self.xp_to_next_level = self._calculate_xp_needed(self.level)
        
    def _calculate_xp_needed(self, level: int) -> int:
        # Fórmula simples de progressão: Nível * 1000
        return level * 1000 
    
    def add_xp(self, amount: int) -> bool:
        """Adiciona XP e retorna True se o jogador subiu de nível."""
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.xp_to_next_level:
            self.level += 1
            self.experience -= self.xp_to_next_level
            self.xp_to_next_level = self._calculate_xp_needed(self.level)
            leveled_up = True
            
        return leveled_up
        
    def get_max_health_for_level(self) -> int:
        level_bonus = self.level * 10
        
        VITALITY_MULTIPLIER = 8
        vitality_bonus = self.vitality * VITALITY_MULTIPLIER
        
        return self.base_health + level_bonus + vitality_bonus

    def get_attack_power(self) -> int:
         return self.strength * 2 
        
    def get_movement_speed(self) -> float:
        return 5.0 + (self.agility * 0.1)