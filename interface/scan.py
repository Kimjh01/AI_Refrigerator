import cv2
from django.urls import reverse
import json
import requests
import uuid
import time
import pygame
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
from django.conf import settings
from datetime import datetime, timedelta
from .models import FoodItem  # models.py에서 정의한 모델 import

# CLOVA OCR API 설정
api_url = settings.CLOVA_OCR_API_URL
secret_key = settings.CLOVA_OCR_SECRET_KEY

# 파일 경로 설정
beep_sound = os.path.join(settings.BASE_DIR, 'interface/static/sounds/beep.mp3')
json_file_path = os.path.join(settings.BASE_DIR, 'interface/static/data/barcode_data.json')
font_path = os.path.join(settings.BASE_DIR, 'interface/static/fonts/PB.otf')

# pygame 초기화
pygame.mixer.init()

def put_korean_text(frame, text, position, font_size=20, color=(0, 255, 0)):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(position, text, font=font, fill=color)
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame

def get_item_data_from_barcode(barcode_data):
    # 바코드 데이터를 통해 제품 정보를 가져오는 로직을 구현하세요.
    try:
        with open(json_file_path, mode="r", encoding="utf-8") as file:
            barcode_data_list = json.load(file)
        for item in barcode_data_list:
            if item.get("BAR_CD") == barcode_data:
                return item
        return None
    except FileNotFoundError:
        print("JSON 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError:
        print("JSON 파일 형식이 올바르지 않습니다.")
    return None

def save_to_database(product_info, user):
    """
    바코드로 스캔한 제품 정보를 데이터베이스에 저장
    """
    try:
        # 기본값 설정
        expiry_days = {
            '실온': 5,  # 실온 보관 시 30일
            '냉장': 7,   # 냉장 보관 시 7일
            '냉동': 9   # 냉동 보관 시 90일
        }
        
        # 상품 정보에서 보관 방법 확인
        storage_type = '냉장'  # 기본값
        if '냉동' in product_info.get('PRDLST_NM', ''):
            storage_type = '냉동'
        elif '실온' in product_info.get('PRDLST_NM', ''):
            storage_type = '실온'

        # 유통기한 계산
        purchase_date = datetime.now().date()
        expiry_date = purchase_date + timedelta(days=expiry_days[storage_type])

        # 데이터베이스에 저장
        food = FoodItem.objects.create(
            user=user,
            name=product_info.get('PRDLST_NM', '알 수 없음'),
            barcode=product_info.get('BAR_CD', ''),
            price=product_info.get('PRICE', 0),  # 가격 정보가 있다면 사용
            quantity=1,  # 기본값
            purchase_date=purchase_date,
            expiry_date=expiry_date,
            storage_type=storage_type,
            category=product_info.get('CATEGORY', '기타'),  # 카테고리 정보가 있다면 사용
            source='barcode'  # source를 'barcode'로 설정
        )
        return {"status": "completed", "food_id": food.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def capture_and_extract_numbers():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"status": "error", "message": "카메라를 열 수 없습니다."}

    start_time = time.time()  # 카운트다운 시작 시간

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 경과 시간에 따른 카운트다운 계산
        elapsed_time = time.time() - start_time
        countdown = int(10 - elapsed_time)  # 10초 카운트다운

        # 카운트다운과 한글 안내 메시지를 OpenCV 화면에 표시
        if countdown > 0:
            frame = put_korean_text(frame, f"촬영까지 {countdown}초", (50, 50), font_size=20, color=(0, 0, 255))
        else:
            frame = put_korean_text(frame, "촬영 중...", (50, 50), font_size=20, color=(0, 255, 0))
            cv2.imshow('Camera', frame)
            cv2.waitKey(1000)  # "촬영 중..." 메시지를 1초 동안 표시
            break  # 카운트다운이 끝나면 촬영 진행

        # 가이드 박스와 추가 안내 메시지
        height, width = frame.shape[:2]
        box_width, box_height = int(width * 0.5), int(height * 0.4)
        x1, y1 = (width - box_width) // 2, (height - box_height) // 2
        x2, y2 = x1 + box_width, y1 + box_height
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        frame = put_korean_text(frame, "박스에 맞게 바코드를 인식시켜주세요.", (x1, y1 - 30), font_size=20)

        # OpenCV 창 업데이트
        cv2.imshow('Camera', frame)
        key = cv2.waitKey(1) & 0xFF

        # 'q' 키로 종료
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return {"status": "cancelled", "message": "촬영이 취소되었습니다."}

        # 'c' 키로 즉시 촬영
        if key == ord('c'):
            break

    # 촬영 소리 재생
    pygame.mixer.music.load(beep_sound)
    pygame.mixer.music.play()

    # 가이드 박스 내 이미지 캡처
    cropped_frame = frame[y1:y2, x1:x2]
    ret, img_encoded = cv2.imencode('.jpg', cropped_frame)
    if not ret:
        cap.release()
        cv2.destroyAllWindows()
        return {"status": "error", "message": "이미지 인코딩 실패"}

    # OCR API 요청 준비
    image_data = img_encoded.tobytes()
    request_json = {
        'images': [{'format': 'jpg', 'name': 'numbers'}],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }
    payload = {'message': json.dumps(request_json).encode('UTF-8')}
    files = [('file', ('image.jpg', image_data, 'image/jpeg'))]
    headers = {'X-OCR-SECRET': secret_key}

    try:
        response = requests.post(api_url, headers=headers, data=payload, files=files)
        response.raise_for_status()
        json_data = response.json()
        extracted_numbers = [field['inferText'] for field in json_data['images'][0]['fields'] if field['inferText'].isdigit()]
        final_barcode = ''.join(extracted_numbers)
        print("최종 바코드:", final_barcode)
    except requests.exceptions.RequestException as e:
        print(f"OCR 요청 실패: {e}")
        final_barcode = None

    cap.release()
    cv2.destroyAllWindows()
    return final_barcode if final_barcode else {"status": "error", "message": "바코드 인식 실패"}


def process_barcode_scan(user):
    """
    바코드 스캔 프로세스를 처리하고 결과를 반환
    """
    try:
        barcode = capture_and_extract_numbers()
        if not barcode:
            return {"status": "error", "message": "바코드를 인식할 수 없습니다."}

        product_info = get_item_data_from_barcode(barcode)
        if not product_info:
            return {"status": "error", "message": "제품 정보를 찾을 수 없습니다."}

        result = save_to_database(product_info, user)
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

# 바코드 스캔 프로세스 시작
if __name__ == "__main__":
    result = process_barcode_scan()
    print(result)
