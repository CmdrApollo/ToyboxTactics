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
        user.health = min(user.health + 5, user.max_health)

        return ("+5", "palegreen")

class PaperArmorItem(Item):
    def __init__(self):
        super().__init__("Paper Armor", 15, False)
    
    def on_use(self, user, target):
        pass

class ThumbtackItem(Item):
    def __init__(self):
        super().__init__("Thumbtack", 15, False)
    
    def on_use(self, user, target):
        pass