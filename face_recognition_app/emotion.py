import cv2
from deepface import DeepFace

# Start webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open webcam")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    try:
        # Analyze frame for emotion
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=True)
        dominant_emotion = result[0]['dominant_emotion']
        print("Detected Emotion:", dominant_emotion)

        # Display on screen
        cv2.putText(frame, dominant_emotion, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    except Exception as e:
        print("No face detected")

    # Show the frame with emotion label
    cv2.imshow("Emotion Detection", frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
