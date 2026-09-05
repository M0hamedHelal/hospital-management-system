import streamlit as st
from datetime import date

from database import init_db
from Models.constants import BLOOD_TYPES, SPECIALIZATIONS
import Services.hospital_service as svc

st.set_page_config(page_title="Al-Amal Hospital", page_icon="🏥", layout="wide")
init_db()

if "auth" not in st.session_state:
    st.session_state.auth = None          # {"role": "doctor" | "patient", "id": "..."}
if "page" not in st.session_state:
    st.session_state.page = "login"       # "login" | "register"


def logout():
    st.session_state.auth = None
    st.session_state.page = "login"


# --------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------- #

def login_view():
    st.title(" Al-Amal Hospital")
    st.subheader("Please login to continue")

    role = st.radio("Login as:", ["Patient", "Doctor"], horizontal=True)
    user_id = st.text_input("Your ID (10 digits)", max_chars=10)

    if st.button("Login", type="primary"):
        if len(user_id) != 10 or not user_id.isdigit():
            st.error("ID must be exactly 10 digits.")
        elif role == "Doctor":
            if svc.doctor_row_by_id(user_id) is None:
                st.error("No doctor found with this ID.")
            else:
                st.session_state.auth = {"role": "doctor", "id": user_id}
                st.rerun()
        else:
            if svc.patient_row_by_id(user_id) is None:
                st.error("No patient found with this ID.")
            else:
                st.session_state.auth = {"role": "patient", "id": user_id}
                st.rerun()

    st.divider()
    st.caption("New here?")
    if st.button("Register a new account"):
        st.session_state.page = "register"
        st.rerun()


# --------------------------------------------------------------------- #
# Register
# --------------------------------------------------------------------- #

def register_view():
    st.title(" Create New Account")
    role = st.radio("Register as:", ["Patient", "Doctor"], horizontal=True)

    # كل حقل ليه key خاص بيه في session_state، عشان نقدر نتحكم فيه إمتى يتمسح.
    field_defaults = {
        "reg_name": "", "reg_id": "", "reg_age": 0, "reg_national_id": "", "reg_phone": "",
        "reg_blood": BLOOD_TYPES[0], "reg_problem": "",
        "reg_spec": SPECIALIZATIONS[0], "reg_start": "09:00", "reg_end": "17:00",
    }
    for key, value in field_defaults.items():
        st.session_state.setdefault(key, value)

    with st.form("register_form"):
        name = st.text_input("Full Name", key="reg_name")
        id_ = st.text_input("ID (10 digits)", max_chars=10, key="reg_id")
        age = st.number_input("Age", min_value=0, max_value=130, step=1, key="reg_age")
        national_id = st.text_input("National ID (14 digits)", max_chars=14, key="reg_national_id")
        phone = st.text_input("Phone (01xxxxxxxxx)", max_chars=11, key="reg_phone")

        if role == "Patient":
            blood = st.selectbox("Blood Type", BLOOD_TYPES, key="reg_blood")
            problem = st.text_area("Problem", key="reg_problem")
        else:
            spec = st.selectbox("Specialization", SPECIALIZATIONS, key="reg_spec")
            c1, c2 = st.columns(2)
            start = c1.text_input("Start Time (HH:MM)", key="reg_start")
            end = c2.text_input("End Time (HH:MM)", key="reg_end")

        submitted = st.form_submit_button("Register", type="primary")

    if submitted:
        try:
            if role == "Patient":
                svc.add_patient(name, id_, int(age), national_id, phone,
                                 st.session_state.reg_blood, st.session_state.reg_problem)
            else:
                svc.add_doctor(name, id_, int(age), national_id, phone,
                                st.session_state.reg_spec, st.session_state.reg_start,
                                st.session_state.reg_end)
            st.success("Registered successfully! You can log in now.")
            for key in field_defaults:
                del st.session_state[key]
            st.rerun()
        except ValueError as e:
            st.error(str(e))
            st.caption("What you typed is still here — just fix the field above and press Register again.")

    st.divider()
    if st.button("Already have an account? Login"):
        st.session_state.page = "login"
        st.rerun()
# --------------------------------------------------------------------- #
# Patient dashboard
# --------------------------------------------------------------------- #

def patient_view(patient_id):
    patient = svc.patient_row_by_id(patient_id)

    top_l, top_r = st.columns([5, 1])
    top_l.title(f"👤 Welcome, {patient['name']}")
    top_l.caption(f"Blood Type: {patient['blood_type']}  |  Problem: {patient['problem']}")
    if top_r.button("Logout"):
        logout()
        st.rerun()

    st.subheader("Book an Appointment")
    specs = svc.list_specializations()
    if not specs:
        st.info("No doctors registered yet.")
    else:
        c1, c2 = st.columns(2)
        spec = c1.selectbox("Specialization", specs)
        doctors = svc.list_doctors_by_specialization(spec)
        doctor_labels = {f"Dr. {d['name']}  ({d['start_time']}–{d['end_time']})": d for d in doctors}

        if not doctor_labels:
            c2.info("No doctors available in this specialization.")
        else:
            doctor_label = c2.selectbox("Doctor", list(doctor_labels.keys()))
            doctor_row = doctor_labels[doctor_label]

            appt_date = st.date_input("Date", min_value=date.today(), value=date.today())
            available = svc.get_available_slots(doctor_row, appt_date.isoformat())

            if not available:
                st.warning("This doctor has no free slots on the selected date.")
            else:
                slot = st.selectbox("Available Slot", available)
                if st.button("Book Appointment", type="primary"):
                    try:
                        svc.book_appointment(doctor_row["id"], patient_id, slot, appt_date.isoformat())
                        st.success("Appointment booked successfully!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    st.divider()
    st.subheader("My Appointments")
    appts = svc.list_patient_appointments(patient_id)
    if not appts:
        st.caption("No appointments yet.")
    for a in appts:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
        c1.write(f"Dr. {a['doctor_name']}  ({a['specialization']})")
        c2.write(a["date"])
        c3.write(a["slot"])
        c4.write(a["status"])
        if a["status"] == "confirmed":
            if c5.button("Cancel", key=f"cancel_{a['id']}"):
                svc.cancel_appointment(a["id"])
                st.rerun()

    st.divider()
    st.subheader("My Medical History")
    history = svc.get_patient_history(patient_id)
    if not history:
        st.caption("No previous prescriptions.")
    for h in history:
        st.write(f"**[{h['date']}]** Dr. {h['doctor_name']}: {h['note']}")


# --------------------------------------------------------------------- #
# Doctor dashboard
# --------------------------------------------------------------------- #

def doctor_view(doctor_id):
    doctor = svc.doctor_row_by_id(doctor_id)

    top_l, top_r = st.columns([5, 1])
    top_l.title(f"🩺 Dr. {doctor['name']}")
    top_l.caption(doctor["specialization"])
    if top_r.button("Logout"):
        logout()
        st.rerun()

    appts = svc.list_doctor_appointments(doctor_id)
    if not appts:
        st.info("No appointments yet.")
        return

    labels = {f"{a['patient_name']}  |  {a['date']} {a['slot']}  |  {a['status']}": a for a in appts}
    selected_label = st.selectbox("Select an appointment", list(labels.keys()))
    appt = labels[selected_label]
    patient = svc.patient_row_by_id(appt["patient_id"])

    st.write(f"**Patient:** {patient['name']}  |  **Blood Type:** {patient['blood_type']}")
    st.write(f"**Problem:** {patient['problem']}")
    st.write(f"**Appointment:** {appt['date']} at {appt['slot']}  |  **Status:** {appt['status']}")

    if appt["status"] == "confirmed":
        note = st.text_area("Prescription / Notes")
        if st.button("Save Prescription", type="primary"):
            try:
                svc.complete_appointment(appt["id"], note)
                st.success("Prescription saved and appointment completed.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    else:
        st.caption(f"This appointment is already {appt['status']}.")

    st.divider()
    st.subheader(f"{patient['name']}'s Medical History")
    history = svc.get_patient_history(patient["id"])
    if not history:
        st.caption("No previous prescriptions.")
    for h in history:
        st.write(f"**[{h['date']}]** Dr. {h['doctor_name']}: {h['note']}")


# --------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------- #

if st.session_state.auth:
    if st.session_state.auth["role"] == "doctor":
        doctor_view(st.session_state.auth["id"])
    else:
        patient_view(st.session_state.auth["id"])
elif st.session_state.page == "register":
    register_view()
else:
    login_view()
