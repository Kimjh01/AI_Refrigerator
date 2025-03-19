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
api_url = 'https://wgx0qbj54o.apigw.ntruss.com/custom/v1/34708/338c935a43532c7781a20459e02703897290a6e9edf0ec92795e6ee78aa3788c/general'
secret_key = 'S2FhQ1NrbWFiZ0lCcHhqVGhHdlJ4cFVJb0RpbEtUd2I='

# 파일 경로 설정
beep_sound = os.path.join(settings.BASE_DIR, 'myapp/static/sounds/beep.mp3')
json_file_path = os.path.join(settings.BASE_DIR, 'myapp/static/data/barcode_data.json')
font_path = os.path.join(settings.BASE_DIR, 'myapp/static/fonts/PB.otf')

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

def save_to_database(product_info):
    """
    바코드로 스캔한 제품 정보를 데이터베이스에 저장
    """
    try:
        # 기본값 설정
        expiry_days = {
            '실온': 30,  # 실온 보관 시 30일
            '냉장': 7,   # 냉장 보관 시 7일
            '냉동': 90   # 냉동 보관 시 90일
        }
        
        # 상품 정보에서 보관 방법 확인
        storage_type = '실온'  # 기본값
        if '냉장' in product_info.get('PRDLST_NM', ''):
            storage_type = '냉장'
        elif '냉동' in product_info.get('PRDLST_NM', ''):
            storage_type = '냉동'

        # 유통기한 계산
        purchase_date = datetime.now().date()
        expiry_date = purchase_date + timedelta(days=expiry_days[storage_type])

        # 데이터베이스에 저장
        food = FoodItem.objects.create(
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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 가이드 박스 좌표 설정
        height, width = frame.shape[:2]
        box_width, box_height = int(width * 0.5), int(height * 0.4)
        x1, y1 = (width - box_width) // 2, (height - box_height) // 2
        x2, y2 = x1 + box_width, y1 + box_height

        # 안내 메시지와 가이드 박스 추가
        frame = put_korean_text(frame, "박스에 맞게 바코드를 인식시켜주세요.", (x1, y1 - 30))
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 카메라 화면 표시
        cv2.imshow('Camera', frame)
        key = cv2.waitKey(30) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('c'):
            # 'c' 키 입력 시 소리 재생
            pygame.mixer.music.load(beep_sound)
            pygame.mixer.music.play()

            # 가이드 박스 내 이미지 캡처
            cropped_frame = frame[y1:y2, x1:x2]
            ret, img_encoded = cv2.imencode('.jpg', cropped_frame)
            if not ret:
                break

            image_data = img_encoded.tobytes()

            # OCR API 요청 생성
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
            except requests.exceptions.RequestException as e:
                print(f"OCR 요청 실패: {e}")
                break

            json_data = response.json()
            extracted_numbers = [field['inferText'] for field in json_data['images'][0]['fields'] if field['inferText'].isdigit()]

            if extracted_numbers:
                final_barcode = ''.join(extracted_numbers)
                print("최종 바코드:", final_barcode)
                
                cap.release()
                cv2.destroyAllWindows()
                return final_barcode
            else:
                print("숫자가 인식되지 않았습니다.")
                cap.release()
                cv2.destroyAllWindows()
                return None

    cap.release()
    cv2.destroyAllWindows()
    return None












def process_barcode_scan():
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

        result = save_to_database(product_info)
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

# 바코드 스캔 프로세스 시작
if __name__ == "__main__":
    result = process_barcode_scan()
    print(result)
