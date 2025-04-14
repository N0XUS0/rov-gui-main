#hazzem task
import cv2 

username = 'admin'  
password = 'Oirov*123'
ip = '192.168.1100.'  
channel = 1 , 2 , 3 , 4
stream = 0  # 0 للـmain stream، 1 للـsub stream

# رابط RTSP
rtsp_url = f'rtsp://{username}:{password}@{ip}/Streaming/Channels/{channel}0{stream}'
# print ('rtsp_url')
# # افتح الكاميرا
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ فشل الاتصال بالكاميرا")
    exit()

print("✅ تم الاتصال بالكاميرا، اضغط Q للخروج")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ لم يتم استلام الإطار من الكاميرا")
        break

    cv2.imshow("كاميرا المراقبة", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
