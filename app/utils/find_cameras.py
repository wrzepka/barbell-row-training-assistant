import cv2


def find_cameras(max_cameras=6):
    found = []

    for i in range(max_cameras):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

        if cap.isOpened():
            ok, frame = cap.read()

            if ok:
                found.append(i)

        cap.release()

    return found


if __name__ == "__main__":
    cameras = find_cameras()
    print(f"Znalezione indeksy: {cameras}")