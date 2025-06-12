class Item:
    def __init__(self, name, price, requires_target):
        self.name = name
        self.price = price
        self.requires_target = requires_target
    
    def on_use(self, user, target):
        pass

class Potion(Item):
    def __init__(self):
        super().__init__("Potion", 8, False)
    
    def on_use(self, user, target):
        user.health = min(user.health + 75, user.max_health)

        return ("+75", "palegreen")