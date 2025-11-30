class ViewportComponent:
    def __init__(self, radius: int = 20):
        self.radius = radius  
        
        self.last_sent_entities = set()

    def __repr__(self):
        return f"<Viewport radius={self.radius} seen={len(self.last_sent_entities)}>"
