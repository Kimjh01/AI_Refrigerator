from django.shortcuts import render
from django.urls import reverse
import json
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
import os
import cv2
from django.conf import settings
from django.contrib import messages
from .forms import FoodItemForm
from .models import FoodItem
from .receipt import capture_and_process_frame
from .scan import process_barcode_scan
from django.shortcuts import get_object_or_404
import logging
from datetime import datetime, timezone, timedelta
from django.utils import timezone


logger = logging.getLogger(__name__)

# 메인 페이지 뷰들
def main_home(request):
    return render(request, 'main_home.html')

def add_food(request):
    return render(request, 'add_food.html')

def recipes(request):
    return render(request, 'recipes.html')


def best_before(request):

    sort_by = request.GET.get('sort_by', 'expiry_date')  # 기본값은 'expiry_date'로 설정
    food_items = FoodItem.objects.all().order_by(sort_by)  # 정렬 기준 적용


    processed_items = []
    for item in food_items:
        processed_item = {
            'id': item.id,
            'name': item.name,
            'purchase_date': item.purchase_date,
            'expiry_date': item.expiry_date,
            'storage_type': item.storage_type,
            'source': item.source,
        }

        if hasattr(item, 'item_data'):
            item_data = item.item_data or {}
            processed_item['source'] = item_data.get('source', item.source)


        logger.debug(f"Processed item source: {processed_item['source']}")
        processed_items.append(processed_item)

    context = {
        'food_items': processed_items,
    }
    return render(request, 'best_before.html', context)

def delete_food_item(request, item_id):
    if request.method == 'POST':
        food_item = get_object_or_404(FoodItem, id=item_id)
        food_item.delete()
        return redirect('best_before')  # 삭제 후 리다이렉트할 페이지

def community(request):
    return render(request, 'community.html')

def profile(request):
    return render(request, 'profile.html')

def test(request):
    return render(request, 'test.html')

def result(request):
    return render(request, 'result.html')


from django.conf import settings
from django.http import JsonResponse
from datetime import datetime
import os
import json
from ultralytics import YOLO
from .models import FoodItem




# YOLO 모델 불러오기
model = YOLO(settings.MODEL_PATH)

CLASS_NAME_MAPPING = {
    "apple": "사과",
    "carrot": "당근",
    "chili": "고추",
    "cucumber": "오이",
    "egg_plant": "가지",
    "onion": "양파",
    "tangerine": "귤",
    "pimento": "파프리카",
    "potato": "감자",
    "spring_onion": "대파",
    "squash": "애호박",
    "tomato": "토마토"
}

def ai_scan(request):
    json_file_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'data', 'detections.json')
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)

    # 기존 JSON 파일에서 데이터 불러오기
    all_detections = []
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                all_detections = json.load(f)
                print("Loaded existing detections from JSON:", all_detections)
        except json.JSONDecodeError:
            all_detections = []  # 파일이 비어 있거나 JSON 형식이 잘못된 경우 빈 리스트로 초기화

    # 중복 방지용으로 기존에 저장된 클래스 목록 확인
    existing_classes = {detection['class_name'] for detection in all_detections}

    # YOLO 감지 시작 (3회 반복)
    cap = cv2.VideoCapture(2)
    for _ in range(3):  # 3회 반복
        ret, frame = cap.read()
        if not ret:
            return JsonResponse({'status': 'error', 'message': '웹캠에서 이미지를 캡처할 수 없습니다.'})

        results = model(frame)
        
        for result in results:
            for obj in result.boxes:
                if obj.conf > 0.6:
                    class_index = int(obj.cls.item())
                    class_name = model.names[class_index]

                    # 중복 클래스 방지
                    if class_name not in existing_classes:
                        detection = {
                            "class_name": class_name,
                            "detection_time": datetime.now().strftime("%Y-%m-%d")
                        }
                        all_detections.append(detection)
                        existing_classes.add(class_name)  # 클래스 추가
                        korean_name = CLASS_NAME_MAPPING.get(class_name, class_name)  # 매핑된 한글 이름 사용

                        # 데이터베이스에 저장
                        purchase_date = timezone.now().date()
                        expiry_date = purchase_date + timedelta(days=7)
                        FoodItem.objects.create(
                            name=korean_name,
                            barcode='',  # 바코드 정보가 없으므로 빈 문자열로 설정
                            price=0,  # 가격 정보가 없으므로 기본값 설정
                            quantity=1,  # 기본값
                            purchase_date=purchase_date,
                            expiry_date=expiry_date,
                            storage_type='',  # 기본값
                            category='기타',  # 기본값
                            source='ai_scan'  # AI 스캔으로 추가된 항목임을 명시
                        )

    cap.release()  # 루프 종료 후 카메라 해제

    # JSON 파일에 저장
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_detections, f, ensure_ascii=False, indent=4)

    return JsonResponse({'status': 'completed', 'detected_classes': list(existing_classes)})




def ai_scan_loading(request):
    return render(request, 'ai_scan_loading.html')

from django.shortcuts import render
import os
import json
from django.conf import settings

# 영어 클래스명을 한국어로 변환하는 매핑
X_CLASS_NAME_MAPPING = {
    "사과": "apple",
    "당근": "carrot",
    "고추": "chili",
    "오이": "cucumber",
    "가지": "egg plant",
    "양파": "onion",
    "귤": "tangerine",
    "파프리카": "pimento",
    "감자": "potato",
    "대파": "spring_onion",
    "애호박": "squash",
    "토마토": "tomato"
}





def ai_scan_result(request):
    # 데이터베이스에서 FoodItem 객체 가져오기
    food_items = FoodItem.objects.filter(source='ai_scan')
    label_expiry = {
        "apple": 30, "carrot": 21, "chili": 14, "cucumber": 7, "egg plant": 7, 
        "onion": 14, "tangerine": 14, "pimento": 5, "potato": 70, 
        "spring_onion": 35, "squash": 6, "tomato": 5
    }

    storage_methods = {
        "onion": "껍질을 벗기고 물기를 제거한 후 랩으로 싸서 보관. 통풍이 잘 되는 서늘한 곳에 보관. 썬 양파는 밀폐용기에 담아 5-7일간 보관 가능",
        "cucumber": "물기를 제거하고 키친타올로 감싼 후 비닐백에 넣어 보관. 꼭지 부분을 위로 향하게 세워서 보관. 자른 오이는 밀폐용기에 담아 3-4일간 보관 가능.",
        "squash": "씻지 않은 상태로 비닐백에 넣어 보관. 자른 애호박은 랩으로 싸서 밀폐용기에 보관. 자른 애호박은 랩으로 싸서 2-3일간 보관 가능.",
        "egg plant": "씻지 않은 상태로 비닐백에 넣어 보관. 자른 가지는 레몬즙을 뿌리고 랩으로 싸서 보관. 자른 가지는 랩으로 싸서 2-3일간 보관 가능.",
        "pimento": "씻지 않은 상태로 비닐백에 넣어 보관. 자른 피망은 밀폐용기에 넣어 보관. 자른 피망은 밀폐용기에 담아 3-4일간 보관 가능.",
        "potato": "통풍이 잘 되는 서늘하고 어두운 곳에 보관. 신문지나 종이봉투에 넣어 보관. 싹이 난 감자는 제거 후 사용. 자른 감자는 물에 담가 냉장 보관 시 1-2일간 유지 가능",
        "tomato": "완숙 토마토는 실온 보관, 덜 익은 토마토는 냉장 보관. 꼭지를 위로 향하게 하여 보관. 자른 토마토는 밀폐용기에 담아 3-4일간 보관 가능.",
        "carrot": "잎을 제거하고 물기를 제거한 후 비닐백에 넣어 보관. 자른 당근은 물에 담가 밀폐용기에 보관. 자른 당근은 물에 담가 냉장 보관 시 1주일간 유지 가능.",
        "spring_onion": "물기를 제거하고 신문지로 감싼 후 비닐백에 넣어 보관. 뿌리 부분을 물에 담가 보관 가능. 자른 대파는 밀폐용기에 넣어 보관.",
        "chili": "씻지 않은 상태로 비닐백에 넣어 보관. 자른 고추는 밀폐용기에 넣어 보관. 에틸렌에 민감하므로 과일과 분리 보관.",
        "apple": "개별 포장하여 냉장고 과일칸에 보관. 에틸렌을 많이 발생시키므로 다른 과일/채소와 분리 보관. 상온에서도 1-2주 보관 가능.",
        "tangerine": "씻지 않은 상태로 비닐백에 넣어 보관. 에틸렌을 발생시키므로 다른 과일/채소와 분리 보관. 상온에서도 1-2주 보관 가능."
    }

    images = []
    for item in food_items:
        purchase_date = item.purchase_date  # datetime.date 객체로 유지
        eng_name = X_CLASS_NAME_MAPPING.get(item.name, item.name)  # 영어 이름으로 매핑
        expiry_days = label_expiry.get(eng_name, 7)  # 기본값을 설정해 예외 방지
        expiry_date = purchase_date + timedelta(days=expiry_days)
        storage_type = storage_methods.get(eng_name, "상세 정보 없음")  # 보관 방법 가져오기

        # 데이터베이스에 업데이트
        item.expiry_date = expiry_date
        item.storage_type = storage_type
        item.save()  # 변경 사항 저장

        images.append({
            "class_name": item.name,
            "image_path": f"{settings.STATIC_URL}yolo_images/{eng_name}.jpg",
            "purchase_date": purchase_date.strftime("%Y-%m-%d"),  # 문자열 포맷으로 변환
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),  # 문자열 포맷으로 변환
            "storage_type": storage_type  # 보관 방법 추가
        })

    return render(request, 'ai_scan_result.html', {'images': images})







from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
from .scan import capture_and_extract_numbers
# search_product_in_json  # 바코드 인식 관련 함수



# 바코드 관련 뷰들
def barcode_loading(request):
    return render(request, 'barcode_loading.html')

def barcode_scan(request):
    """
    바코드 스캔 페이지를 보여주는 뷰
    """
    return render(request, 'barcode_scan.html')

def barcode_scan_process(request):
    """
    바코드 스캔 프로세스를 처리하는 뷰
    """
    result = process_barcode_scan()
    
    if result["status"] == "completed":
        food_id = result["food_id"]
        messages.success(request, "상품이 성공적으로 등록되었습니다.")
        return JsonResponse({
            'status': 'completed',
            'redirect_url': reverse('barcode_result', args=[food_id])
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': result.get("message", "바코드 처리 중 오류가 발생했습니다.")
        })
    



# # 바코드 인식 작업 수행 - 유정 버전
# def barcode_scan_process(request):
#     # 바코드 인식 함수 실행
#     barcode = capture_and_extract_numbers()  # 바코드 추출 함수
#     if barcode:
#         product_info = search_product_in_json(barcode)  # 바코드를 이용해 제품 정보 조회
#         if product_info:
#             # 성공 시 제품 정보와 날짜를 세션에 저장
#             request.session['product_info'] = product_info
#             # request.session['capture_date'] = datetime.now().strftime("%Y.%m.%d")
#             return JsonResponse({'status': 'completed', 'redirect_url': '/barcode_result/'})
#         else:
#             return JsonResponse({'status': 'error', 'message': '제품 정보를 찾을 수 없습니다.'})
#     else:
#         return JsonResponse({'status': 'error', 'message': '바코드를 인식하지 못했습니다.'})



def barcode_result(request, food_id):
    try:
        food = FoodItem.objects.get(id=food_id)
        product_info = food.item_data  # item_data 필드에서 제품 정보를 가져옵니다.
        capture_date = food.created_at.strftime("%Y-%m-%d")  # 생성 날짜를 캡처 날짜로 사용합니다.
        
        context = {
            'product_info': product_info,
            'capture_date': capture_date,
            'food':food,
        }
        return render(request, 'barcode_result.html', context)
    except FoodItem.DoesNotExist:
        messages.error(request, "해당 상품을 찾을 수 없습니다.")
        return redirect('home')  # 또는 다른 적절한 페이지로 리다이렉트


def barcode_edit(request, food_id):
    """
    스캔된 상품 정보를 수정하는 뷰
    """
    try:
        food = Food.objects.get(id=food_id)
        if request.method == 'POST':
            food.name = request.POST.get('name', food.name)
            food.quantity = int(request.POST.get('quantity', food.quantity))
            food.expiry_date = request.POST.get('expiry_date', food.expiry_date)
            food.storage_type = request.POST.get('storage_type', food.storage_type)
            food.category = request.POST.get('category', food.category)
            food.save()
            
            messages.success(request, "상품 정보가 수정되었습니다.")
            return redirect('barcode_result', food_id=food_id)
        else:
            context = {
                'food': food,
            }
            return render(request, 'barcode_edit.html', context)
            
    except Food.DoesNotExist:
        messages.error(request, "상품을 찾을 수 없습니다.")
        return redirect('barcode_scan')

# 영수증 관련 뷰들
def receipt_loading(request):
    return render(request, 'receipt_loading.html')

def run_capture_and_process(request):
    result = capture_and_process_frame()
    if result.get("status") == "completed":
        return JsonResponse({'status': 'completed', 'redirect_url': '/receipt_result/'})
    else:
        return JsonResponse({
            'status': 'error', 
            'message': result.get("message", "영수증 인식 중 오류가 발생했습니다.")
        })


def receipt_result(request):
    try:
        # 모든 데이터 가져오기 (또는 필요한 필터 적용)
        ocr_data = FoodItem.objects.all().order_by('-id')[:10]
        
        # ocr_data를 템플릿에 전달
        context = {
            'ocr_data': ocr_data,
        }
        return render(request, 'receipt_result.html', context)
    except Exception as e:
        # 오류 처리
        return render(request, 'receipt_result.html', {'error': str(e)})

# 요리 관련 뷰들
def cook_loading1(request):
    return render(request, 'cook_loading1.html')

def cook_loading2(request):
    return render(request, 'cook_loading2.html')

def cook_loading3(request):
    return render(request, 'cook_loading3.html')

def cook_loading4(request):
    return render(request, 'cook_loading4.html')

def cook_loading5(request):
    return render(request, 'cook_loading5.html')

def cook_loading6(request):
    return render(request, 'cook_loading6.html')

# def cook_result(request):
#     return render(request, 'cook_result.html')

def cook_result1(request):
    return render(request, 'cook_result1.html')

def cook_result2(request):
    return render(request, 'cook_result2.html')

def cook_result3(request):
    return render(request, 'cook_result3.html')

def cook_result4(request):
    return render(request, 'cook_result4.html')

def cook_result5(request):
    return render(request, 'cook_result5.html')

def cook_result6(request):
    return render(request, 'cook_result6.html')


def allergy(request):
    return render(request, 'allergy.html')

def low_calorie(request):
    return render(request, 'low_calorie.html')

def low_income(request):
    return render(request, 'low_income.html')

# 카메라 관련 뷰들
def open_camera_2(request):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return render(request, 'error.html', {"message": "카메라를 열 수 없습니다."})

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Camera', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return redirect('next_page_2')

def next_page_2(request):
    return render(request, 'receipt_result.html')

# 요리 결과 관련 뷰들
def ncook_result1(request, variable):
    return render(request, 'cook_result1.html', {'variable': variable})

def ncook_result2(request, variable):
    return render(request, 'cook_result1.html', {'variable': variable})

def choice(request):
    return render(request, 'choice.html')

# 수동 입력 관련 뷰들
def manual_input(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            # form.save()를 사용하여 폼 데이터를 저장합니다.
            form.save()
            return redirect('manual_result')
    else:
        form = FoodItemForm()

    return render(request, 'manual_input.html', {'form': form})


def manual_result(request):
    #food_items = FoodItem.objects.all().order_by('-created_at')
    food_items = FoodItem.objects.all()
    context = {'food_items': food_items}
    return render(request, 'manual_result.html', {'food_items': food_items})

def toggle_keyboard(request):
    """가상 키보드 토글을 처리하는 뷰"""
    import subprocess
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'show':
            subprocess.Popen(['matchbox-keyboard'])
            return JsonResponse({'status': 'success', 'message': 'Keyboard shown'})
        elif action == 'hide':
            subprocess.call(['pkill', 'matchbox-keyboard'])
            return JsonResponse({'status': 'success', 'message': 'Keyboard hidden'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})












from django.shortcuts import render, redirect
from .models import Note
from .forms import NoteForm

def note_view(request):
    notes = Note.objects.all()
    form = NoteForm()
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('note_view')
    return render(request, 'note.html', {'form': form, 'notes': notes})



def drawing_page(request):
    return render(request, 'note_draw.html')







# views.py
import json
import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import os

@csrf_exempt
def save_drawing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # JSON 데이터 파싱
            imgstr = data.get('image').split(';base64,')[1]  # image 데이터 확인
            img_data = base64.b64decode(imgstr)
            
            # 파일 이름 생성 및 저장 경로 설정
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            file_name = f"drawing_{timestamp}.png"
            file_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'community', file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 이미지 저장
            with open(file_path, 'wb') as f:
                f.write(img_data)
            
            return JsonResponse({'status': 'success', 'file_name': file_name})
        
        except Exception as e:
            print(f"Error saving image: {e}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    
    return JsonResponse({'status': 'fail', 'message': 'Invalid request method'}, status=400)






# views.py
def community(request):
    # 저장된 이미지 경로를 불러옵니다
    drawing_images = os.listdir(os.path.join(settings.BASE_DIR, 'myapp', 'static', 'community'))
    drawing_images = [f"community/{img}" for img in drawing_images]

    context = {
        'drawing_images': drawing_images,
    }
    return render(request, 'community.html', context)