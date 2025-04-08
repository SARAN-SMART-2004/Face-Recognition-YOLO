import cv2
import face_recognition
import numpy as np
import os
import pandas as pd
from datetime import datetime
from django.core.files.base import ContentFile
from .models import KnownPerson, UnknownPerson
from django.core.mail import EmailMessage
from django.conf import settings




def send_known_person_email(email, name):
    """Send email notification to known person when marked present."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Attendance Marked - {name}"
    body = f"Hello {name},\n\nYour attendance has been recorded successfully on {now}.\n\nThank you.\nFace Recognition System"

    email_msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[email],
    )
    try:
        email_msg.send(fail_silently=False)
        print(f"📧 Sent attendance email to {name} ({email})")
    except Exception as e:
        print(f"❌ Failed to send email to {name}: {str(e)}")


def get_excel_filename():
    """Generate today's Excel filename (YYYY-MM-DD.xlsx)."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{today}.xlsx"

def load_existing_logs():
    """Load logs from today's Excel file or create a new DataFrame."""
    filename = get_excel_filename()
    if os.path.exists(filename):
        return pd.read_excel(filename)
    return pd.DataFrame(columns=["Time", "Name"])

from .models import Attendance
from django.utils.timezone import now as dj_now

def save_to_excel(name):
    now = datetime.now().strftime("%H:%M:%S")
    in_time=datetime.now().strftime("%H:%M:%S")
    out_time="-"
    today_date = datetime.now().date()
    filename = get_excel_filename()

    df = load_existing_logs()

    # Avoid duplicate Excel logging
    if not (df["Name"] == name).any():
        new_entry = pd.DataFrame([[now, name,in_time,out_time]], columns=["Time", "Name","IN Time","OUT Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(filename, index=False)
        print(f"✔ Logged {name} at {now} in {filename}")

    # Save to DB only once per day
    if not Attendance.objects.filter(name=name, date=today_date,in_time=in_time).exists():
        Attendance.objects.create(name=name, timestamp=dj_now(),in_time=in_time)
        print(f"✔ Logged {name} in DB at {dj_now()}")


def send_unknown_face_email(image_bytes, name):
    """Send an email to admin with unknown face image."""
    subject = f"Unknown Person Detected - {name}"
    body = f"An unknown person '{name}' was detected by the system. The image is attached."

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.ADMIN_EMAIL],
    )
    email.attach(f"{name}.jpg", image_bytes, 'image/jpeg')
    email.send(fail_silently=False)

def recognize_faces_webcam():
    video_capture = cv2.VideoCapture(0)

    known_people = KnownPerson.objects.all()
    known_encodings = []
    known_names = []

    # Load known encodings
    for person in known_people:
        encoding = np.frombuffer(person.encoding, dtype=np.float64)
        if encoding.size == 128:
            known_encodings.append(encoding)
            known_names.append(person.name)

    # Load unknowns from DB
    unknown_people = UnknownPerson.objects.all()
    unknown_encodings = []
    unknown_labels = {}

    for unknown in unknown_people:
        encoding = np.frombuffer(unknown.encoding, dtype=np.float64)
        if encoding.size == 128:
            unknown_encodings.append(encoding)
            unknown_labels[unknown.id] = unknown.label

    unknown_counter = len(unknown_people) + 1
    tolerance = 0.6  # Adjust if needed

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠ Could not access webcam!")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"

            # First try matching with known faces
            if known_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance)
                if True in matches:
                    matched_index = matches.index(True)
                    name = known_names[matched_index]
                    
                    # Get the matched person object
                    person = known_people[matched_index]
                    
                    # Save attendance only if not already marked
                    df = load_existing_logs()
                    if not (df["Name"] == name).any():
                        send_known_person_email(person.email, name)


            # If not matched with known
            if name == "Unknown":
                distances = face_recognition.face_distance(unknown_encodings, face_encoding)
                if len(distances) > 0 and np.min(distances) < tolerance:
                    matched_index = np.argmin(distances)
                    unknown_id = list(unknown_labels.keys())[matched_index]
                    name = unknown_labels[unknown_id]
                    print(f"[MATCHED] Existing Unknown: {name} (Distance: {np.min(distances):.4f})")
                else:
                    name = f"Unknown{unknown_counter}"
                    unknown_counter += 1

                    # Save image
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_bytes = buffer.tobytes()
                    unknown_image = ContentFile(image_bytes, name=f"{name}.jpg")

                    new_unknown = UnknownPerson(label=name, encoding=face_encoding.tobytes())
                    new_unknown.image.save(f"{name}.jpg", unknown_image)
                    new_unknown.save()

                    # Update in-memory unknowns to avoid duplicate
                    unknown_encodings.append(face_encoding)
                    unknown_labels[new_unknown.id] = name

                    print(f"[NEW UNKNOWN] Saved: {name}")
                    send_unknown_face_email(image_bytes, name)

            # Save attendance only once per person per day
            if name.startswith("Unknown"):
                save_unknown_attendance(name)
            else:
                save_to_excel(name)


            # Draw rectangle and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    

def save_unknown_attendance(name):
    today_date = datetime.now().date()
    now_time = datetime.now().strftime("%H:%M:%S")

    # Check if attendance for this unknown label is already marked today
    if not Attendance.objects.filter(name=name, date=today_date).exists():
        Attendance.objects.create(name=name, timestamp=dj_now(), in_time=now_time)
        print(f"✔ Logged unknown {name} in DB at {dj_now()}")
        
        # Also log to Excel
        filename = get_excel_filename()
        df = load_existing_logs()
        new_entry = pd.DataFrame([[now_time, name, now_time, "-"]], columns=["Time", "Name", "IN Time", "OUT Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(filename, index=False)
        print(f"✔ Logged {name} in Excel at {now_time}")
    else:
        print(f"⚠ {name} already marked today, skipping duplicate")
