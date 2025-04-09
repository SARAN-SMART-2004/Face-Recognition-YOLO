import cv2
import face_recognition
import numpy as np
import os
import pandas as pd
from datetime import datetime
from django.core.files.base import ContentFile
from .models import KnownPerson, UnknownPerson, Attendance
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.timezone import now as dj_now
from deepface import DeepFace


def send_email(subject, body, recipient):
    email_msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[recipient],
    )
    try:
        email_msg.send(fail_silently=False)
        print(f"📧 Email sent to {recipient}")
    except Exception as e:
        print(f"❌ Email failed to {recipient}: {str(e)}")


def send_known_person_email(email, name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Attendance Marked - {name}"
    body = f"Hello {name},\n\nYour IN time has been recorded at {now}.\n\nThank you.\nFace Recognition System"
    send_email(subject, body, email)


def send_out_time_email(email, name, out_time):
    subject = f"OUT Time Recorded - {name}"
    body = f"Hello {name},\n\nYour OUT time has been recorded at {out_time}.\n\nThank you.\nFace Recognition System"
    send_email(subject, body, email)


def send_unknown_face_email(image_bytes, name):
    subject = f"Unknown Person Detected - {name}"
    body = f"An unknown person '{name}' was detected by the system. The image is attached."
    email = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
    email.attach(f"{name}.jpg", image_bytes, 'image/jpeg')
    email.send(fail_silently=False)


def get_excel_filename():
    return f"{datetime.now().strftime('%Y-%m-%d')}.xlsx"


def load_existing_logs():
    filename = get_excel_filename()
    return pd.read_excel(filename) if os.path.exists(filename) else pd.DataFrame(columns=["Time", "Name", "IN Time", "OUT Time"])


def save_to_excel(name, email=None):
    now_time = datetime.now().strftime("%H:%M:%S")
    today_date = datetime.now().date()
    filename = get_excel_filename()
    df = load_existing_logs()

    if not Attendance.objects.filter(name=name, date=today_date).exists():
        Attendance.objects.create(name=name, timestamp=dj_now(), in_time=now_time)
        new_entry = pd.DataFrame([[now_time, name, now_time, "-"]], columns=["Time", "Name", "IN Time", "OUT Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(filename, index=False)
        print(f"✔ Logged {name} at {now_time} in Excel & DB")
        if email:
            send_known_person_email(email, name)
    else:
        print(f"⚠ {name} already marked today, skipping duplicate")


def save_unknown_attendance(name):
    now_time = datetime.now().strftime("%H:%M:%S")
    today_date = datetime.now().date()

    if not Attendance.objects.filter(name=name, date=today_date).exists():
        Attendance.objects.create(name=name, timestamp=dj_now(), in_time=now_time)
        df = load_existing_logs()
        new_entry = pd.DataFrame([[now_time, name, now_time, "-"]], columns=["Time", "Name", "IN Time", "OUT Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(get_excel_filename(), index=False)
        print(f"✔ Logged unknown {name} in Excel & DB")
    else:
        print(f"⚠ {name} already marked today, skipping duplicate")


def update_out_time(name, email=None):
    now_time = datetime.now().strftime("%H:%M:%S")
    today_date = datetime.now().date()
    try:
        attendance = Attendance.objects.filter(name=name, date=today_date).latest('timestamp')
        if not attendance.out_time:
            attendance.out_time = now_time
            attendance.save()

            df = load_existing_logs()
            df.loc[df["Name"] == name, "OUT Time"] = now_time
            df.to_excel(get_excel_filename(), index=False)
            print(f"🕒 OUT time marked for {name} at {now_time}")
            if email:
                send_out_time_email(email, name, now_time)
        else:
            print(f"⚠ OUT time already marked for {name}")
    except Attendance.DoesNotExist:
        print(f"⚠ No record found to update OUT time for {name}")


def recognize_faces_webcam():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    known_people = KnownPerson.objects.all()
    known_encodings = [np.frombuffer(p.encoding, dtype=np.float64) for p in known_people if len(np.frombuffer(p.encoding, dtype=np.float64)) == 128]
    known_names = [p.name for p in known_people]
    known_emails = {p.name: p.email for p in known_people}

    unknown_people = UnknownPerson.objects.all()
    unknown_encodings = [np.frombuffer(u.encoding, dtype=np.float64) for u in unknown_people if len(np.frombuffer(u.encoding, dtype=np.float64)) == 128]
    unknown_labels = {u.id: u.label for u in unknown_people}
    unknown_counter = len(unknown_people) + 1

    recognized_person = None
    tolerance = 0.6

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Webcam not accessible")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance)
            face_crop = frame[top:bottom, left:right]
            emotion = None

            try:
                analysis = DeepFace.analyze(face_crop, actions=['emotion'], enforce_detection=False)
                emotion = analysis[0]['dominant_emotion']
            except Exception as e:
                print(f"⚠ Emotion detection error: {e}")

            if True in matches:
                idx = matches.index(True)
                name = known_names[idx]
                recognized_person = name
                if emotion:
                    if not Attendance.objects.filter(name=name, date=datetime.now().date()).exists():
                        save_to_excel(name, known_emails.get(name))
                    elif emotion.lower() == 'happy':
                        update_out_time(name, known_emails.get(name))
            else:
                distances = face_recognition.face_distance(unknown_encodings, face_encoding)
                if distances.size and np.min(distances) < tolerance:
                    idx = np.argmin(distances)
                    name = unknown_labels[list(unknown_labels.keys())[idx]]
                else:
                    name = f"Unknown{unknown_counter}"
                    unknown_counter += 1
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_bytes = buffer.tobytes()
                    unknown_image = ContentFile(image_bytes, name=f"{name}.jpg")
                    new_unknown = UnknownPerson(label=name, encoding=face_encoding.tobytes())
                    new_unknown.image.save(f"{name}.jpg", unknown_image)
                    new_unknown.save()
                    unknown_encodings.append(face_encoding)
                    unknown_labels[new_unknown.id] = name
                    send_unknown_face_email(image_bytes, name)
                recognized_person = name
                save_unknown_attendance(name)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            if emotion:
                cv2.putText(frame, emotion, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)

        cv2.imshow("Face & Emotion Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()