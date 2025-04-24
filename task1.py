import cv2
import numpy as np
import os
import time

def capture_images(output_folder, num_images, target_size, rtsp_url):
    """التقاط الصور من كاميرا RTSP عند الضغط على زر المسطرة"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("❌ لم يتم الاتصال بالكاميرا.")
        return

    print("اضغط على المسطرة (Space) لالتقاط صورة. اضغط 'q' للخروج.")
    captured_count = 0

    cv2.namedWindow("Hikvision Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hikvision Camera", 1920, 1080)

    while captured_count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("❌ فشل في قراءة الإطار من الكاميرا.")
            break

        cv2.imshow("Hikvision Camera", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 32:  # زر المسطرة
            img_path = os.path.join(output_folder, f"image({captured_count + 1}).jpeg")
            resized_frame = cv2.resize(frame, target_size)
            cv2.imwrite(img_path, resized_frame)
            print(f"✅ تم حفظ الصورة رقم {captured_count + 1}: {img_path}")
            captured_count += 1

    cap.release()
    cv2.destroyAllWindows()


def load_images_from_folder(folder, target_size):
    images = []
    filenames = sorted(
        [f for f in os.listdir(folder) if ''.join(filter(str.isdigit, f))],
        key=lambda x: int(''.join(filter(str.isdigit, x)))
    )
    for filename in filenames:
        img_path = os.path.join(folder, filename)
        if filename.endswith('.jpeg') or filename.endswith('.png'):
            img = cv2.imread(img_path)
            if img is not None:
                img_resized = cv2.resize(img, target_size)
                images.append(img_resized)
    return images


def create_seamless_panorama(images, overlap=100):
    h, w, c = images[0].shape
    panorama_width = w * len(images) - overlap * (len(images) - 1)
    panorama = np.zeros((h, panorama_width, c), dtype=np.uint8)

    for i, img in enumerate(images):
        x_offset = i * (w - overlap)
        for y in range(h):
            for x in range(w):
                if x_offset + x < panorama.shape[1]:
                    alpha = (x / overlap) if x < overlap else 1
                    panorama[y, x_offset + x] = (
                        panorama[y, x_offset + x] * (1 - alpha) + img[y, x] * alpha
                    ).astype(np.uint8)
    return panorama


def create_rows_of_panorama(images, images_per_row, overlap=100):
    rows = []
    for i in range(0, len(images), images_per_row):
        row_images = images[i:i + images_per_row]
        if len(row_images) == images_per_row:
            row_panorama = create_seamless_panorama(row_images, overlap)
            rows.append(row_panorama)
    return rows


def stack_rows(rows):
    return np.vstack(rows)


# إعدادات
folder_path = r"C:\Users\REDACO\New folder\rov-gui-main2025\captured_images"
target_size = (640, 480)
output_image_path = "panorama_with_rows.jpg"
num_images_to_capture = 5
rtsp_url = "rtsp://admin:Oirov*123@192.168.1.200:554/Streaming/Channels/101"

# التقاط الصور من كاميرا RTSP
capture_images(folder_path, num_images_to_capture, target_size, rtsp_url)

# تحميل الصور
images = load_images_from_folder(folder_path, target_size)

if len(images) >= 5:
    selected_images = images[:5]
    rows = create_rows_of_panorama(selected_images, images_per_row=5, overlap=100)
    final_image = stack_rows(rows)
    cv2.imwrite(output_image_path, final_image)
    print(f"✅ تم إنشاء بانوراما من 5 صور وحفظها في {output_image_path}")
else:
    print("❗ يجب أن يحتوي المجلد على 5 صور على الأقل.")
