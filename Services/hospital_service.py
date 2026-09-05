"""
Business logic layer. Everything the GUI needs goes through here.

This replaces the old in-memory Hospital/Booking classes. The important
fix compared to the original project: availability and booking are now
calculated PER DATE. In the old version a doctor's "09:00" slot became
permanently unavailable after a single booking, for every future date,
because slots were tracked only by time-of-day. Here, `appointments` are
stored with their date, and the UNIQUE(doctor_id, slot, date) constraint
in the database is what actually prevents double-booking the same
doctor at the same date+time.
"""

import sqlite3
from datetime import datetime, date as date_cls

from Models.Doctor import Doctor
from Models.Patient import Patient
from database import get_connection


# --------------------------------------------------------------------- #
# Doctors
# --------------------------------------------------------------------- #

def add_doctor(name, id, age, nationalID, phone, specialization, startTime, endTime):
    doctor = Doctor(name, id, age, nationalID, phone, specialization, startTime, endTime)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO doctors (id, name, age, national_id, phone, specialization, start_time, end_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (doctor.id, doctor.name, doctor.age, doctor.nationalID, doctor.phone,
             doctor.specialization, doctor.startTime, doctor.endTime),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("A doctor with this ID or National ID already exists")
    finally:
        conn.close()
    return doctor_row_by_id(doctor.id)


def doctor_row_by_id(doctor_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    conn.close()
    return row


def list_doctors():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    conn.close()
    return rows


def list_specializations():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization").fetchall()
    conn.close()
    return [r["specialization"] for r in rows]


def list_doctors_by_specialization(specialization):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM doctors WHERE specialization = ? ORDER BY name", (specialization,)
    ).fetchall()
    conn.close()
    return rows


# --------------------------------------------------------------------- #
# Patients
# --------------------------------------------------------------------- #

def add_patient(name, id, age, nationalID, phone, bloodType, problem):
    patient = Patient(name, id, age, nationalID, phone, bloodType, problem)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO patients (id, name, age, national_id, phone, blood_type, problem)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (patient.id, patient.name, patient.age, patient.nationalID, patient.phone,
             patient.bloodType, patient.problem),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("A patient with this ID or National ID already exists")
    finally:
        conn.close()
    return patient_row_by_id(patient.id)


def patient_row_by_id(patient_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return row


# --------------------------------------------------------------------- #
# Availability & booking  (the fixed, per-date logic)
# --------------------------------------------------------------------- #

def _all_daily_slots(doctor_row):
    doctor = Doctor(
        name=doctor_row["name"], id=doctor_row["id"], age=doctor_row["age"],
        nationalID=doctor_row["national_id"], phone=doctor_row["phone"],
        specialization=doctor_row["specialization"],
        startTime=doctor_row["start_time"], endTime=doctor_row["end_time"],
    )
    return doctor.generate_slots()


def get_booked_slots(doctor_id, date_str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT slot FROM appointments WHERE doctor_id = ? AND date = ? AND status = 'confirmed'",
        (doctor_id, date_str),
    ).fetchall()
    conn.close()
    return {r["slot"] for r in rows}


def get_available_slots(doctor_row, date_str):
    """Slots for THIS doctor on THIS specific date only."""
    all_slots = _all_daily_slots(doctor_row)
    booked = get_booked_slots(doctor_row["id"], date_str)
    return [s for s in all_slots if s not in booked]


def _validate_date(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError("Date must be in YYYY-MM-DD format")
    if d < date_cls.today():
        raise ValueError("Appointment date cannot be in the past")
    return d


def book_appointment(doctor_id, patient_id, slot, date_str):
    doctor_row = doctor_row_by_id(doctor_id)
    patient_row = patient_row_by_id(patient_id)
    if doctor_row is None:
        raise ValueError("Doctor not found")
    if patient_row is None:
        raise ValueError("Patient not found")

    _validate_date(date_str)

    if slot not in _all_daily_slots(doctor_row):
        raise ValueError("This slot is outside the doctor's working hours")

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO appointments (doctor_id, patient_id, slot, date, status) "
            "VALUES (?, ?, ?, ?, 'confirmed')",
            (doctor_id, patient_id, slot, date_str),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # This is the database-level guarantee: same doctor + same slot + same date = rejected.
        raise ValueError("This slot is already booked on this date")
    finally:
        conn.close()

    return get_appointment_by_ids(doctor_id, patient_id, slot, date_str)


def get_appointment_by_ids(doctor_id, patient_id, slot, date_str):
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM appointments
           WHERE doctor_id=? AND patient_id=? AND slot=? AND date=?
           ORDER BY id DESC LIMIT 1""",
        (doctor_id, patient_id, slot, date_str),
    ).fetchone()
    conn.close()
    return row


def get_appointment(appointment_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    conn.close()
    return row


def cancel_appointment(appointment_id):
    appt = get_appointment(appointment_id)
    if appt is None:
        raise ValueError("Appointment not found")
    if appt["status"] != "confirmed":
        raise ValueError("Only confirmed appointments can be cancelled")

    conn = get_connection()
    conn.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()


def complete_appointment(appointment_id, note):
    appt = get_appointment(appointment_id)
    if appt is None:
        raise ValueError("Appointment not found")
    if appt["status"] != "confirmed":
        raise ValueError("Only confirmed appointments can be completed")
    if not note or not note.strip():
        raise ValueError("A note is required to complete the appointment")

    doctor_row = doctor_row_by_id(appt["doctor_id"])

    conn = get_connection()
    conn.execute("UPDATE appointments SET status = 'completed' WHERE id = ?", (appointment_id,))
    conn.execute(
        "INSERT INTO medical_records (patient_id, doctor_name, note, date) VALUES (?, ?, ?, ?)",
        (appt["patient_id"], doctor_row["name"], note.strip(), appt["date"]),
    )
    conn.commit()
    conn.close()


def list_doctor_appointments(doctor_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, p.name AS patient_name, p.blood_type, p.problem
           FROM appointments a JOIN patients p ON a.patient_id = p.id
           WHERE a.doctor_id = ? ORDER BY a.date, a.slot""",
        (doctor_id,),
    ).fetchall()
    conn.close()
    return rows


def list_patient_appointments(patient_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, d.name AS doctor_name, d.specialization
           FROM appointments a JOIN doctors d ON a.doctor_id = d.id
           WHERE a.patient_id = ? ORDER BY a.date, a.slot""",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


def get_patient_history(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM medical_records WHERE patient_id = ? ORDER BY date DESC, id DESC",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows
