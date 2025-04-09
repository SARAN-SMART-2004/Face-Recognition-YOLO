from django.apps import AppConfig
import threading
import os
import platform
   

class FaceRecognitionAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'face_recognition_app'

    def ready(self):
        def play_startup_sound():
            try:
                if platform.system() == 'Windows':
                    import winsound
                    winsound.PlaySound('start.wav', winsound.SND_FILENAME)
                else:
                    from playsound import playsound
                    playsound(os.path.join(os.path.dirname(__file__), 'start.wav'))
                print("🔔 Startup sound played.")
            except Exception as e:
                print(f"⚠ Failed to play startup sound: {str(e)}")

        threading.Thread(target=play_startup_sound).start()