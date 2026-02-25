class Teacher:
    def teach(self):
        print("Teacher teaches students")

class Student1(Teacher):
    def play(self):
        print("Student1 plays")

class Student2(Teacher):
    def sing(self):
        print("Student2 sings")

s1 = Student1()
s2 = Student2()

s1.teach()
s2.teach()