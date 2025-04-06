import cv2
import face_recognition
import numpy as np
import os
from django.core.files.base import ContentFile
from .models import KnownPerson, UnknownPerson
from datetime import datetime

def recognize_faces_webcam():
    video_capture = cv2.VideoCapture(0)

    known_people = KnownPerson.objects.all()
    known_encodings = []
    known_names = []

    # Load known encodings
    for person in known_people:
        encoding = np.frombuffer(person.encoding, dtype=np.float64)
        if encoding.size == 128:  # Ensure valid encoding
            known_encodings.append(encoding)
            known_names.append(person.name)

    # Fetch existing unknown persons from DB
    unknown_people = UnknownPerson.objects.all()
    unknown_encodings = []
    unknown_labels = {}

    for unknown in unknown_people:
        encoding = np.frombuffer(unknown.encoding, dtype=np.float64)
        if encoding.size == 128:
            unknown_encodings.append(encoding)
            unknown_labels[unknown.id] = unknown.label

    unknown_counter = len(unknown_people) + 1  # Start numbering unknowns

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
                # Check if this unknown face was detected before
                matches = face_recognition.compare_faces(unknown_encodings, face_encoding)
                if True in matches:
                    matched_index = matches.index(True)
                    name = unknown_labels[list(unknown_labels.keys())[matched_index]]
                else:
                    # Assign a new unknown label
                    name = f"Unknown{unknown_counter}"
                    unknown_counter += 1
                    
                    # Save unknown face to DB
                    _, buffer = cv2.imencode('.jpg', frame)
                    unknown_image = ContentFile(buffer.tobytes(), name=f"{name}.jpg")

                    new_unknown = UnknownPerson(label=name, encoding=face_encoding.tobytes())
                    new_unknown.image.save(f"{name}.jpg", unknown_image)
                    new_unknown.save()

                    # Update stored unknowns
                    unknown_encodings.append(face_encoding)
                    unknown_labels[new_unknown.id] = name

            # Draw rectangle and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
