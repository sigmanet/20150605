__author__ = 'TMagill'

class character:
    def __init__(self):
        self.weapon = 'bare hands'
    def equip(self,newWeapon):
        self.weapon = newWeapon
    def attack(self):
        print 'You attack with your', self.weapon

bob = character()

bob.attack()
bob.equip('gun')
bob.attack()