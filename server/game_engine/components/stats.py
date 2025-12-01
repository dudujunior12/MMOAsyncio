from typing import Dict


class StatsComponent:
    def __init__(self, 
                 level: int = 1, 
                 experience: int = 0,
                 stat_points: int = 0,
                 base_health: int = 100,
                 strength: int = 1,
                 agility: int = 1,
                 vitality: int = 1,
                 intelligence: int = 1,
                 dexterity: int = 1,
                 luck: int = 1,
                 class_bonus: Dict[str, int] | None = None
                ):
        self.level = level
        self.experience = experience
        self.base_health = base_health
        self.stat_points = stat_points
        self.strength = strength
        self.agility = agility
        self.vitality = vitality
        self.intelligence = intelligence
        self.dexterity = dexterity
        self.luck = luck
        self.speed_multiplier = 1.0
        
        self.xp_to_next_level = self._calculate_xp_needed(self.level)
        
        self.class_bonus = class_bonus or {
            "strength": 0,
            "agility": 0,
            "vitality": 0,
            "intelligence": 0,
            "dexterity": 0,
            "luck": 0
        }
        
    def _calculate_xp_needed(self, level: int) -> int:
        # Fórmula simples de progressão: Nível * 1000
        return level * 1000 
    
    def add_xp(self, amount: int) -> bool:
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.xp_to_next_level:
            self.level += 1
            self.experience -= self.xp_to_next_level
            self.xp_to_next_level = self._calculate_xp_needed(self.level)
            
            # --- LÓGICA RAGNAROK: GANHAR PONTOS AO UPAR ---
            self.stat_points += 5 # Ganha 5 pontos por nível
            leveled_up = True
            
        return leveled_up
        
    # --- Helpers para obter valores "totais" (base + classe) ---
    def get_total(self, stat_name: str) -> int:
        base = getattr(self, stat_name)
        bonus = self.class_bonus.get(stat_name, 0)
        return base + bonus

    @property
    def total_strength(self) -> int:
        return self.get_total("strength")

    @property
    def total_agility(self) -> int:
        return self.get_total("agility")

    @property
    def total_vitality(self) -> int:
        return self.get_total("vitality")

    @property
    def total_intelligence(self) -> int:
        return self.get_total("intelligence")

    @property
    def total_dexterity(self) -> int:
        return self.get_total("dexterity")

    @property
    def total_luck(self) -> int:
        return self.get_total("luck")

    # Máx HP baseado em base_health (classe) + level + vitalidade total
    def get_max_health_for_level(self) -> int:
        level_bonus = self.level * 10
        vitality_multiplier = 8
        vitality_bonus = self.total_vitality * vitality_multiplier
        return self.base_health + level_bonus + vitality_bonus

    # Se preferir nome genérico:
    def get_max_health(self) -> int:
        return self.get_max_health_for_level()

    # ataque baseado na força total
    def get_attack_power(self):
        return (self.total_strength * 2) + (self.total_dexterity // 5)

    def get_movement_speed(self) -> float:
        base_speed = 5.0 + (self.total_agility * 0.1)
        # Aplica o multiplicador de buffs ou poções
        return base_speed * self.speed_multiplier