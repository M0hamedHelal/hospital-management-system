# 🏥 Al-Amal Hospital Management System

A desktop-grade hospital management application built in **Python**, with a **Streamlit** web interface and a persistent **SQLite** database. The project is designed as a clean, layered system that demonstrates solid **Object-Oriented Programming (OOP)** principles combined with a practical **separation-of-concerns architecture**.

---

##  Overview

The system supports two types of users — **Patients** and **Doctors** — who register and log in with a unique 10-digit ID. Patients can book appointments with doctors by specialization, view their upcoming appointments, and check their medical history. Doctors can view their schedule, complete appointments, and write prescriptions/notes that become part of the patient's permanent medical record.

Unlike a typical beginner CRUD project, this system was deliberately re-engineered to fix a critical real-world bug: **appointment slots are now tracked per date**, not just per time-of-day — enforced at the database level, not just in application code.

---

##  Architecture

The project follows a **4-layer, separation-of-concerns architecture**:

```
┌─────────────────────────────────────────────┐
│  Presentation Layer        → app.py          │  Streamlit UI, routing, session state
├─────────────────────────────────────────────┤
│  Service / Business Layer  → Services/       │  All business rules & workflows
├─────────────────────────────────────────────┤
│  Domain / Model Layer      → Models/         │  OOP entities & validation rules
├─────────────────────────────────────────────┤
│  Persistence Layer         → database.py     │  SQLite schema, connections
└─────────────────────────────────────────────┘
```

**Why this matters:**
- The **UI never talks to the database directly** — it only calls functions in `Services/hospital_service.py`.
- The **Service layer never worries about validation rules** — that responsibility belongs entirely to the **Model layer** (`Person`, `Doctor`, `Patient`).
- The **Model layer never worries about storage** — it just represents a valid, well-formed entity in memory.
- The **Database layer** is the single source of truth for uniqueness and integrity constraints (via `PRIMARY KEY` / `UNIQUE`), rather than trusting application code alone.

This makes the codebase easy to extend: adding a new feature (e.g., billing) means adding a table in `database.py`, a model in `Models/`, and functions in `Services/`, without ever touching the UI logic for existing features.

### Project structure

```
hospital-management-system/
│
├── app.py                     # Streamlit UI — entry point of the application
├── database.py                # SQLite schema definition & connection handling
│
├── Models/
│   ├── Person.py               # Abstract base class — shared validation logic
│   ├── Doctor.py               # Inherits Person — working hours & slot generation
│   ├── Patient.py               # Inherits Person — blood type & medical problem
│   └── constants.py            # Fixed reference data (blood types, specializations)
│
├── Services/
│   └── hospital_service.py     # Business logic: registration, booking, cancellation, prescriptions
│
├── requirements.txt
└── hospital.db                 # Auto-generated SQLite database file
```

---

## 🎯 OOP Principles in Practice

| Principle | Where it's applied |
|---|---|
| **Abstraction** | `Person` is an `ABC` (Abstract Base Class) with an abstract `get_info()` method — it can never be instantiated directly, only through its subclasses. |
| **Inheritance** | `Doctor` and `Patient` both extend `Person`, reusing shared attributes (`name`, `id`, `age`, `nationalID`, `phone`) and validation logic instead of duplicating it. |
| **Encapsulation** | All core attributes are private (`__name`, `__id`, `__age`, etc.) and exposed only through Python `@property` getters/setters, so every assignment is validated (e.g., ID must be 10 digits, phone must start with `01` and be 11 digits, age must be 0–130). |
| **Polymorphism** | Both `Doctor.get_info()` and `Patient.get_info()` override the same abstract method with role-specific behavior. |
| **Single Responsibility** | Each class/module has exactly one reason to change: `Models` = validation, `Services` = business rules, `database.py` = persistence, `app.py` = presentation. |

Example — `Person` enforces validation for every subclass automatically:

```python
class Person(ABC):
    @property
    def age(self):
        return self.__age

    @age.setter
    def age(self, age):
        if age is None or age < 0 or age > 130:
            raise ValueError("Age must be a realistic value (0-130)")
        self.__age = age

    @abstractmethod
    def get_info(self):
        pass
```

---

##  Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | **Python 3** | Core application logic |
| UI / Frontend | **Streamlit** (`>=1.32`) | Web-based interactive interface, forms, session state, routing |
| Database | **SQLite 3** (built-in `sqlite3` module) | Zero-config, file-based relational database (`hospital.db`) |
| Data Access | Raw parameterized SQL via `sqlite3.Row` | Dictionary-like row access without an ORM |
| Design Patterns | Layered architecture, Abstract Base Classes, Property-based encapsulation | Maintainability & correctness |

No external database server or ORM is required — the entire persistence layer is a single portable `.db` file, making the project easy to run and deploy (including free hosting on **Streamlit Community Cloud**).

---

## 🗄️ Database Design

The database consists of **4 tables**, connected through foreign keys:

```sql
doctors            (id PK, name, age, national_id UNIQUE, phone, specialization, start_time, end_time)
patients           (id PK, name, age, national_id UNIQUE, phone, blood_type, problem)
appointments       (id PK, doctor_id FK, patient_id FK, slot, date, status, UNIQUE(doctor_id, slot, date))
medical_records    (id PK, patient_id FK, doctor_name, note, date)
```

**Key design decisions:**

1. **`UNIQUE(doctor_id, slot, date)` on `appointments`** — this is the core fix of the project. Availability is calculated *per specific date*, so booking a doctor's 9:00 AM slot on one day no longer blocks that same slot on every other day (a bug present in the original in-memory version).
2. **`PRIMARY KEY` / `UNIQUE` constraints** on `doctors.id`, `patients.id`, and `national_id` push uniqueness enforcement down to the database engine itself, instead of relying on fragile in-memory tracking (e.g., a class-level `used_ids` set) that could get corrupted by failed validations.
3. **Foreign keys** (`doctor_id`, `patient_id`) tie appointments and medical records back to their owning entities, with `PRAGMA foreign_keys = ON` enabled on every connection.
4. **Status field** (`confirmed` / `cancelled` / `completed`) models the appointment lifecycle without deleting historical data.
5. **`medical_records`** is an append-only audit trail of every completed visit, forming each patient's permanent medical history.

---

## ✨ Features

-  Simple ID-based login/registration for both Patients and Doctors
-  Appointment booking with real, date-aware slot availability
-  Appointment cancellation
-  Doctor-written prescriptions/notes on completed visits
-  Full patient medical history view (for both the patient and their doctors)
-  Database-enforced protection against double-booking and duplicate IDs

---

##  Getting Started

```bash
# 1. Clone and enter the project
cd hospital-management-system

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`. Register a Doctor and a Patient from the **Register** page, then log in using the same 10-digit ID.

To reset the database at any time during development:

```bash
python database.py    # recreates tables if missing
# or simply delete hospital.db — it's recreated automatically on next run
```

---

##  Deployment

Since the database is a single SQLite file with no external server dependency, the app can be deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the project to GitHub (keep `hospital.db` out of version control via `.gitignore`).
2. Connect your GitHub account at [share.streamlit.io](https://share.streamlit.io).
3. Select the repository and set `app.py` as the entry point.
4. Get a live public URL to share in your portfolio.

---

##  Author

**Mohamed Helal** — Educational project demonstrating OOP design, layered architecture, and relational database modeling in Python.