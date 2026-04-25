import cv2

print("Szukam kamer...\n")

found = []
for i in range(6):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        ok, frame = cap.read()
        status = f"OK  ({frame.shape[1]}x{frame.shape[0]})" if ok else "otwarta, ale brak obrazu"
        print(f"  Kamera {i}: {status}")
        found.append(i)
    else:
        print(f"  Kamera {i}: brak")
    cap.release()

print(f"\nZnalezione indeksy: {found}")
print("Ustaw LAPTOP_CAM_INDEX i DROIDCAM_INDEX w training_view.py")
