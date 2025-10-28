class HealthComponent:
    def __init__(self, max_health: int = 100, initial_health: int = None):
        self.max_health = max_health
        if initial_health is not None:
            self.current_health = initial_health
        else:
            self.current_health = max_health
        self.is_dead = False
        
    def take_damage(self, amount: int) -> int:
        if self.is_dead:
            return 0
        
        self.current_health -= amount
        
        if self.current_health <= 0:
            self.current_health = 0
            self.is_dead = True
            
        return amount
    
    def heal(self, amount: int) -> int:
        if self.is_dead:
            return 0
        
        old_health = self.current_health
        self.current_health += amount
        
        if self.current_health > self.max_health:
            self.current_health = self.max_health
            
        return self.current_health - old_health
        
    def __repr__(self):
        return f"Health({self.current_health}/{self.max_health})"