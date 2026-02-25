class Grandfather:
    def land(self):
        print("Grandfather owns land")

class Father(Grandfather):
    def house(self):
        print("Father owns house")

class Son(Father):
    def bike(self):
        print("Son owns bike")

s = Son()
s.land()
s.house()
s.bike()