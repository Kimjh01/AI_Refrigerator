import cv2
import requests
import uuid
import time
import os


    
def capture_and_process_frame():
    # OpenCV를 사용하여 카메라 열기
    cap = cv2.VideoCapture(0)  # 0은 기본 카메라를 의미합니다.

    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        # 프레임을 화면에 표시
        cv2.imshow('Camera', frame)

        # 키 입력을 대기
        key = cv2.waitKey(10) & 0xFF

        # 'q' 키를 누르면 종료
        if key == ord('q'):
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

capture_and_process_frame()
