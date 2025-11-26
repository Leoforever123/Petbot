import cv2
 
# Configuration
address = "udp://localhost:5555"
 
# Access video
cap = cv2.VideoCapture(0)
 
if not cap.isOpened():
    raise Exception("no video stream")
 
while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
 
# Release resources
cap.release()
cv2.destroyAllWindows()
