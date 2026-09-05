from datetime import datetime, timedelta

from Models.Person import Person


class Doctor(Person):
    SLOT_MINUTES = 15

    def __init__(self, name, id, age, nationalID, phone, specialization, startTime, endTime):
        super().__init__(name, id, age, nationalID, phone)
        self.specialization = specialization
        self.startTime, self.endTime = self.__validate_working_hours(startTime, endTime)

    @property
    def specialization(self):
        return self.__specialization

    @specialization.setter
    def specialization(self, value):
        if not value:
            raise ValueError("Specialization is required")
        self.__specialization = value

    def __validate_working_hours(self, startTime, endTime):
        try:
            start = datetime.strptime(startTime, "%H:%M")
            end = datetime.strptime(endTime, "%H:%M")
        except (ValueError, TypeError):
            raise ValueError(
                "Working hours must be in 24-hour HH:MM format (e.g. 09:00, 14:00)"
            )

        if end <= start:
            raise ValueError("End time must be after start time")
        return startTime, endTime

    def generate_slots(self):
        """All possible time-of-day slots for this doctor (independent of any date)."""
        slots = []
        current = datetime.strptime(self.startTime, "%H:%M")
        end = datetime.strptime(self.endTime, "%H:%M")
        while current < end:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=self.SLOT_MINUTES)
        return slots

    def get_info(self):
        return f"Doctor: {self.name} | Specialization: {self.specialization} | Phone: {self.phone}"
