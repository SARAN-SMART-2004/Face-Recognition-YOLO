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

def save_to_excel(name):
    """Save detected face to Excel (Time, Name) if not already logged today."""
    now = datetime.now().strftime("%H:%M:%S")
    filename = get_excel_filename()

    df = load_existing_logs()

    # Check if the name is already logged today
    if not (df["Name"] == name).any():
        new_entry = pd.DataFrame([[now, name]], columns=["Time", "Name"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(filename, index=False)
        print(f"✔ Logged {name} at {now} in {filename}")

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

    # Load unknowns
    unknown_people = UnknownPerson.objects.all()
    unknown_encodings = []
    unknown_labels = {}

    for unknown in unknown_people:
        encoding = np.frombuffer(unknown.encoding, dtype=np.float64)
        if encoding.size == 128:
            unknown_encodings.append(encoding)
            unknown_labels[unknown.id] = unknown.label

    unknown_counter = len(unknown_people) + 1

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

            if known_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                if True in matches:
                    matched_index = matches.index(True)
                    name = known_names[matched_index]

            if name == "Unknown":
                matches = face_recognition.compare_faces(unknown_encodings, face_encoding)
                if True in matches:
                    matched_index = matches.index(True)
                    name = unknown_labels[list(unknown_labels.keys())[matched_index]]
                else:
                    name = f"Unknown{unknown_counter}"
                    unknown_counter += 1

                    # Save image to DB
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_bytes = buffer.tobytes()
                    unknown_image = ContentFile(image_bytes, name=f"{name}.jpg")

                    new_unknown = UnknownPerson(label=name, encoding=face_encoding.tobytes())
                    new_unknown.image.save(f"{name}.jpg", unknown_image)
                    new_unknown.save()

                    unknown_encodings.append(face_encoding)
                    unknown_labels[new_unknown.id] = name

                    # Send email to admin
                    send_unknown_face_email(image_bytes, name)

            # Save only one log per day per person
            save_to_excel(name)

            # Draw label on face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
