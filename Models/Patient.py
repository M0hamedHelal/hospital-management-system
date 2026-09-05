from Models.Person import Person


class Patient(Person):
    def __init__(self, name, id, age, nationalID, phone, bloodType, problem):
        super().__init__(name, id, age, nationalID, phone)
        self.bloodType = bloodType
        self.problem = problem

    @property
    def bloodType(self):
        return self.__bloodType

    @bloodType.setter
    def bloodType(self, value):
        if not value:
            raise ValueError("Blood type is required")
        self.__bloodType = value

    @property
    def problem(self):
        return self.__problem

    @problem.setter
    def problem(self, value):
        if not value:
            raise ValueError("Problem description is required")
        self.__problem = value

    def get_info(self):
        return f"Name: {self.name} | Age: {self.age} | Problem: {self.problem}"
