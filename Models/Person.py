# Pillars of OOP used here: Abstraction & Encapsulation
from abc import ABC, abstractmethod


class Person(ABC):
    def __init__(self, name, id, age, nationalID, phone):
        self.name = name
        self.__set_id(id)
        self.age = age
        self.nationalID = nationalID
        self.set_phone(phone)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        if not name or not isinstance(name, str):
            raise ValueError("Invalid name")
        self.__name = name

    @property
    def id(self):
        return self.__id

    def __set_id(self, id):
        # NOTE: uniqueness is enforced by the database (PRIMARY KEY), not here.
        # This only validates the *format* of the id.
        if not id or len(id) != 10 or not id.isdigit():
            raise ValueError("ID must be 10 digits")
        self.__id = id

    @property
    def age(self):
        return self.__age

    @age.setter
    def age(self, age):
        if age is None or age < 0 or age > 130:
            raise ValueError("Age must be a realistic value (0-130)")
        self.__age = age

    @property
    def nationalID(self):
        return self.__nationalID

    @nationalID.setter
    def nationalID(self, nationalID):
        if not nationalID or len(nationalID) != 14 or not nationalID.isdigit():
            raise ValueError("National ID must be 14 digits")
        self.__nationalID = nationalID

    @property
    def phone(self):
        return self.__phone

    def set_phone(self, phone):
        if not phone or len(phone) != 11 or not phone.isdigit() or phone[0:2] != "01":
            raise ValueError("Invalid phone number")
        self.__phone = phone

    def __str__(self):
        return f"Name: {self.name}, ID: {self.id}, Age: {self.age}, National ID: {self.nationalID}"

    @abstractmethod
    def get_info(self):
        pass
