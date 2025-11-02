class ClassComponent:
    """
    Componente que define a identidade da classe do jogador e sua árvore de evolução.
    """
    def __init__(self, class_name: str):
        self.class_name = class_name
        
    def __repr__(self):
        return f"ClassComponent(Class: {self.class_name})"