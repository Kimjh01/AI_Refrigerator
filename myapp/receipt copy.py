import cv2
import json
import requests
import uuid
import time
import pygame
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import openai
import os
from django.conf import settings
from datetime import datetime
from .models import FoodItem  # models.py에서 정의한 모델 import

# 기존 설정 부분은 동일
api_url = 'https://wgx0qbj54o.apigw.ntruss.com/custom/v1/34708/338c935a43532c7781a20459e02703897290a6e9edf0ec92795e6ee78aa3788c/general'
secret_key = 'S2FhQ1NrbWFiZ0lCcHhqVGhHdlJ4cFVJb0RpbEtUd2I='
openai.api_key = 'sk-None-cCGlsb243LSy5PLctJEJT3BlbkFJmxS4PQX3KTrZBwAcJScY'
beep_sound = os.path.join(settings.BASE_DIR, 'myapp/static/sounds/beep.mp3')
font_path = os.path.join(settings.BASE_DIR, 'myapp/static/fonts/PB.otf')

pygame.mixer.init()

def put_korean_text(frame, text, position, font_size=20, color=(0, 255, 0)):
    # 기존 함수 내용 동일
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(position, text, font=font, fill=color)
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame

def save_to_database(data):
    try:
        # 각 상품 항목을 데이터베이스에 저장
        for item in data['items']:
            FoodItem.objects.create(
                name=item['item_name'],
                price=item['unit_price'],
                quantity=item['quantity'],
                purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),  # 기본값으로 구매일 설정
                storage_type='실온',  # 기본값 설정
                category='기타',  # 기본값 설정
                source='receipt',
                item_data=item  # JSON 필드에 전체 아이템 데이터 저장
            )
        return True
    except Exception as e:
        print(f"데이터베이스 저장 중 오류 발생: {str(e)}")
        return False


def capture_and_process_frame():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"status": "error", "message": "카메라를 열 수 없습니다."}

        while True:
            ret, frame = cap.read()
            if not ret:
                cap.release()
                return {"status": "error", "message": "프레임을 읽을 수 없습니다."}

            frame = put_korean_text(frame, "영수증을 인식시켜주세요.", (20, 20))
            cv2.imshow('Camera', frame)
            key = cv2.waitKey(10) & 0xFF
            
            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return {"status": "error", "message": "작업이 취소되었습니다."}
            
            if key == ord('c'):
                pygame.mixer.music.load(beep_sound)
                pygame.mixer.music.play()

                _, img_encoded = cv2.imencode('.jpg', frame)
                image_data = img_encoded.tobytes()

                # OCR API 요청
                request_json = {
                    'images': [{'format': 'jpg', 'name': 'receipt'}],
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
                except requests.exceptions.RequestException:
                    cap.release()
                    cv2.destroyAllWindows()
                    return {"status": "error", "message": "OCR 요청 실패"}

                json_data = response.json()

                if 'images' not in json_data or not json_data['images'][0]['fields']:
                    cap.release()
                    cv2.destroyAllWindows()
                    return {"status": "error", "message": "인식된 텍스트가 없습니다."}

                # ChatGPT 분석
                string_result = ' '.join([field['inferText'] for field in json_data['images'][0]['fields']])
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
    {
        "role": "system",
        "content": (
            "You are a highly precise assistant that processes receipt information. "
            "If any product name starts with 'P' followed by Korean characters, remove the 'P' at the beginning of that name. "
            "Return only valid JSON format with the following fields: 'purchase_date' (YYYY-MM-DD format), and 'items' (array of products). "
            "Each product in 'items' should have: 'item_name' (product name), 'item_code' (optional), 'unit_price' (price per unit), "
            "'quantity', and 'total_price'. Ensure strict adherence to this format without any additional text. "
            "Only include items that are clearly food products and safe for human consumption, such as groceries, fresh produce, meat, dairy, snacks, and beverages. "
            "Do not include any non-food items, and ignore any items related to trash, such as trash bags."
        )
    },
    {
        "role": "user",
        "content": f'Analyze the following text and return the data in JSON format: {string_result}'
    }
]

                    )
                    message = response['choices'][0]['message']['content']
                    parsed_data = json.loads(message)

                    # 데이터베이스에 저장
                    if save_to_database(parsed_data):
                        cap.release()
                        cv2.destroyAllWindows()
                        return {"status": "completed", "redirect_url": "/receipt_result/"}
                    else:
                        return {"status": "error", "message": "데이터베이스 저장 실패"}

                except Exception as e:
                    cap.release()
                    cv2.destroyAllWindows()
                    return {"status": "error", "message": f"데이터 처리 중 오류 발생: {str(e)}"}

    except Exception as e:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        return {"status": "error", "message": f"예기치 않은 오류가 발생했습니다: {str(e)}"}



