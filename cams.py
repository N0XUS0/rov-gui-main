import cv2

rtsp_url = "rtsp://admin:Oirov*123@192.168.1.200:554/Streaming/Channels/101"
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("NOT CONNECTED")
else:
    cv2.namedWindow("Hikvision Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hikvision Camera", 1920, 1080)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("NOT CONNECTED CAM")
            break

        cv2.imshow("Hikvision Camera", frame)

        if cv2.waitKey(1) == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()