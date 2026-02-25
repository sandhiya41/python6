class Grandpa:
    def property(self):
        print("Grandpa property")

class Father(Grandpa):
    def business(self):
        print("Father business")

class Mother:
    def gold(self):
        print("Mother gold")

class Child(Father, Mother):
    def education(self):
        print("Child education")

c = Child()
c.property()
c.business()
c.gold()
c.education()