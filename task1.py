
import cv2
import numpy as np
import os

def load_images_from_folder(folder, target_size):
    images = []
    filenames = sorted(os.listdir(folder), key=lambda x: int(x.split('(')[-1].split(')')[0]))  # ترتيب الصور رقميًا
    for filename in filenames:
        img_path = os.path.join(folder, filename)
        if filename.endswith('.jpeg') or filename.endswith('.png'):
            img = cv2.imread(img_path)
            if img is not None:
                # ضبط أبعاد الصورة
                img_resized = cv2.resize(img, target_size)
                images.append(img_resized)
    return images

def create_seamless_panorama(images, overlap=100):
    """إنشاء صورة بانورامية بتداخل سلس"""
    h, w, c = images[0].shape
    panorama_width = w * len(images) - overlap * (len(images) - 1)  # العرض النهائي
    panorama = np.zeros((h, panorama_width, c), dtype=np.uint8)

    for i, img in enumerate(images):
        x_offset = i * (w - overlap)
        for y in range(h):
            for x in range(w):
                if x_offset + x < panorama.shape[1]:
                    alpha = (x / overlap) if x < overlap else 1  # تدريج التداخل
                    panorama[y, x_offset + x] = (
                        panorama[y, x_offset + x] * (1 - alpha) + img[y, x] * alpha
                    ).astype(np.uint8)
    return panorama

def create_rows_of_panorama(images, images_per_row, overlap=100):
    """إنشاء صفوف متداخلة من الصور"""
    rows = []
    for i in range(0, len(images), images_per_row):
        row_images = images[i:i + images_per_row]
        if len(row_images) == images_per_row:  # تأكد من أن الصف يحتوي على العدد المطلوب من الصور
            row_panorama = create_seamless_panorama(row_images, overlap)
            rows.append(row_panorama)
    return rows

def stack_rows(rows):
    """دمج الصفوف عموديًا في صورة واحدة"""
    return np.vstack(rows)

# مسار الصور
folder_path = r"C:\Users\REDACO\New folder\rov\img's"
target_size = (640, 480)  # حجم الصور
output_image_path = "panorama_with_rows.jpg"

# تحميل الصور
images = load_images_from_folder(folder_path, target_size)

if len(images) >= 24:
    selected_images = images[:24]  # اختيار أول 24 صورة فقط

    # إنشاء ثلاثة صفوف، كل صف يحتوي على 8 صور متداخلة
    rows = create_rows_of_panorama(selected_images, images_per_row=8, overlap=100)

    # دمج الصفوف في صورة واحدة
    final_image = stack_rows(rows)

    # حفظ الصورة النهائية
    cv2.imwrite(output_image_path, final_image)
    print(f"تم إنشاء صورة تحتوي على 3 صفوف متداخلة وحفظها في {output_image_path}")
else:
    print("يجب أن يحتوي المجلد على 24 صورة على الأقل.")
