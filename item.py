class Item:
    def __init__(self, name, requires_target):
        self.name = name
        self.requires_target = requires_target
    
    def on_use(self, user, target):
        pass

class Potion(Item):
    def __init__(self):
        super().__init__("Potion", False)
    
    def on_use(self, user, target):
        user.health = min(user.health + 5, user.max_health)

        return ("+5", "palegreen")