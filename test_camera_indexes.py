import cv2

print("Testing camera indexes 0, 1, 2...")
for idx in range(3):
    cap = cv2.VideoCapture(idx)
    ret, frame = cap.read()
    print(f"Camera {idx} opened:", ret)
    cap.release()
