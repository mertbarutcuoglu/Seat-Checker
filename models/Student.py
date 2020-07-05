class Student:
    def __init__(self, name, surname, email):
        self.name = name
        self.surname = surname
        self.email = email

    def __eq__(self, other):
        if not isinstance(other, Student):
            return NotImplemented

        return self.email == other.email

    def __hash__(self):
        return hash(self.email)