import cv2
import face_recognition
import numpy as np
from .models import KnownPerson

def recognize_faces_webcam():
    video_capture = cv2.VideoCapture(0)

    known_people = KnownPerson.objects.all()
    known_encodings = []
    known_names = []

    # Load known encodings
    for person in known_people:
        encoding = np.frombuffer(person.encoding, dtype=np.float64)
        if encoding.size == 128:  # Ensure the encoding is valid
            known_encodings.append(encoding)
            known_names.append(person.name)

    if not known_encodings:
        print("⚠ No trained faces found! Upload and train images first.")
        return

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠ Could not access webcam!")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            if len(known_encodings) == 0:
                name = "Unknown"
            else:
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    matched_index = matches.index(True)
                    name = known_names[matched_index]

            # Draw rectangle and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
