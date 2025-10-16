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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)

# 메인 페이지 뷰들
@login_required
def main_home(request):
    return render(request, 'main_home.html')

def add_food(request):
    return render(request, 'add_food.html')

def recipes(request):
    return render(request, 'recipes.html')


@login_required
def best_before(request):

    sort_by = request.GET.get('sort_by', 'expiry_date')  # 기본값은 'expiry_date'로 설정
    food_items = FoodItem.objects.filter(user=request.user).order_by(sort_by)  # 정렬 기준 적용


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

@login_required
def delete_food_item(request, item_id):
    if request.method == 'POST':
        food_item = get_object_or_404(FoodItem, id=item_id, user=request.user)
        food_item.delete()
        return redirect('best_before')  # 삭제 후 리다이렉트할 페이지

def community(request):
    return render(request, 'community.html')



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
    json_file_path = os.path.join(settings.BASE_DIR, 'interface', 'static', 'data', 'detections.json')
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
    cap = cv2.VideoCapture(0)
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
                            user=request.user,
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
    food_items = FoodItem.objects.filter(source='ai_scan', user=request.user)
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

@login_required
def barcode_scan_process(request):
    """
    바코드 스캔 프로세스를 처리하는 뷰
    """
    result = process_barcode_scan(request.user)
    
    if result["status"] == "completed":
        food_item = FoodItem.objects.get(id=result["food_id"])
        food_item.user = request.user
        food_item.save()
        messages.success(request, "상품이 성공적으로 등록되었습니다.")
        return JsonResponse({
            'status': 'completed',
            'redirect_url': reverse('barcode_result', args=[food_item.id])
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
        food = FoodItem.objects.get(id=food_id, user=request.user)
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

@login_required
def run_capture_and_process(request):
    result = capture_and_process_frame(request.user)
    if result.get("status") == "completed":
        return JsonResponse({'status': 'completed', 'redirect_url': '/receipt_result/'})
    else:
        return JsonResponse({
            'status': 'error', 
            'message': result.get("message", "영수증 인식 중 오류가 발생했습니다.")
        })


@login_required
def receipt_result(request):
    try:
        # 모든 데이터 가져오기 (또는 필요한 필터 적용)
        ocr_data = FoodItem.objects.filter(user=request.user).order_by('-id')[:10]
        
        # ocr_data를 템플릿에 전달
        context = {
            'ocr_data': ocr_data,
        }
        return render(request, 'receipt_result.html', context)
    except Exception as e:
        # 오류 처리
        return render(request, 'receipt_result.html', {'error': str(e)})

# 요리 관련 뷰들
@login_required
def cook_loading(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result')})

@login_required
def cook_loading1(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result1')})

@login_required
def cook_loading2(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result2')})

@login_required
def cook_loading3(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result3')})

@login_required
def cook_loading4(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result4')})

@login_required
def cook_loading5(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result5')})

@login_required
def cook_loading6(request):
    return render(request, 'cook_loading_generic.html', {'redirect_url': reverse('cook_result6')})

RECIPES_DATA = {
    'cook_result': {
        'name': '불고기',
        'image': 'images/bulgogi.jpg',
        'ingredients': [
            '소고기 500g',
            '양파 1개 (채 썰기)',
            '대파 1대 (어슷 썰기)',
            '당근 1/2개 (슬라이스)',
            '참기름 1T',
            '참깨 약간',
        ],
        'instructions': [
            '양념장을 만든다.<br><span class="font-bold">[양념]</span> 간장 4T, 설탕 2T, 다진 마늘 1T, 배즙 1/4컵, 맛술 2T, 참기름 1T, 후추 약간',
            '소고기를 양념에 재워 30분간 둔다.',
            '센 불에서 고기를 볶는다.',
            '야채를 넣고 함께 볶아 마무리한다.',
        ],
        'tips': [
            '배즙 대신 사과즙을 사용하면 부드러운 단맛을 더할 수 있습니다.',
            '매운맛을 원하면 청양고추를 추가해보세요.',
            '남은 불고기는 볶음밥이나 김밥 재료로 활용할 수 있습니다.',
        ]
    },
    'cook_result1': {
        'name': '갈비찜',
        'image': 'images/galbi.png',
        'ingredients': [
            '소갈비 1.5kg',
            '무 1/2개 (두툼하게 썰기)',
            '당근 1개 (둥글게 썰기)',
            '양파 1개 (굵게 썰기)',
            '표고버섯 4~5개 (불려서 준비)',
            '대파 2대 (어슷 썰기)',
        ],
        'instructions': [
            '갈비를 찬물에 2시간 동안 담가 핏물을 제거합니다.',
            '끓는 물에 갈비를 5분 정도 데친 후 찬물에 헹궈 불순물을 제거합니다.',
            '양념장을 만듭니다. (간장 1/2컵, 설탕 2T, 다진 마늘 2T, 다진 생강 1t, 배즙 1/2컵, 맛술 2T, 참기름 1T, 후추 약간)',
            '갈비에 양념장을 넣고 30분~1시간 재워 둡니다.',
            '냄비에 무와 당근을 깔고, 양념된 갈비를 올립니다.',
            '갈비가 우둑하게 잠길 만큼 물을 붓고 중불에서 40분간 끓입니다.',
            '양파, 표고버섯, 대파를 넣고 약한 불에서 20분 더 끓입니다.',
            '갈비가 부드러워지고 국물이 걸쭉해지면 완성입니다.',
        ],
        'tips': [
            '더 매콤한 맛을 원한다면 청양고추를 추가하세요.',
            '배 대신 사과즙을 사용해도 특유의 맛을 낼 수 있습니다.',
            '식힌 후 재가열하면 맛이 더욱 깊어집니다.',
        ]
    },
    'cook_result2': {
        'name': '나야 들기름, 무 스테이크',
        'image': 'images/radishsteak.png',
        'ingredients': [
            '통무',
            '가쓰오부시 육수 (또는 물) 800ml',
            '국간장 40ml',
            '맛술 40ml',
        ],
        'instructions': [
            '통무를 2cm 두께로 자릅니다.',
            '겉질에 질긴 섬유질이 많아 두껍게 돌려 깎아줍니다.<br>냄비에 무를 넣고 무가 잠길 정도로 쌀뜨물을 붓습니다.',
            '쌀뜨물에 삶으면 무가 부드럽게 익고 조직이 부스러지는 것을 막아줍니다.<br>(쌀뜨물은 두 번째 씻어낸 물부터 사용합니다.)',
            '무를 부드럽게 삶은 후 찔러보아 \'쑤욱\' 들어가면 완성입니다.',
            '삶은 무의 겉면을 흐르는 물에 조심스럽게 씻어냅니다.',
            '가쓰오부시 육수, 국간장, 맛술을 섞어 끓입니다. 여기에 닭껍질 20g을 넣어 풍미를 더해줍니다.',
            '육수가 끓어오르면 약불로 줄이고 삶은 무를 넣어 간을 들입니다.',
            '무를 10분간 끓인 후 간을 조절합니다. 처음부터 양념을 세게 하면 무가 익기 전에 양념이 짜질 수 있습니다.',
        ],
        'tips': [
            '무를 뜨거운 팬에 구워 겉면을 살짝 그을리면 더욱 맛있습니다.',
            '구운 무를 밥 위에 올려 스테이크처럼 즐길 수 있습니다.',
        ]
    },
    'cook_result3': {
        'name': '간단한 간장 계란밥',
        'image': 'images/ganjangegg.png',
        'ingredients': [
            '밥 1공기',
            '달걀 2개',
            '진간장 2숟가락',
            '참기름 1숟가락',
            '물 2숟가락',
        ],
        'instructions': [
            '그릇에 참기름 ➡️ 간장 ➡️ 달걀 ➡️ 물 순서로 넣습니다.',
            '전자레인지에 1분 40초 동안 돌립니다.',
            '익은 계란을 밥 위에 올립니다.',
        ],
        'tips': [
            '달걀 노른자는 터트려 넣어야 터지지 않고 안전하게 익습니다.',
            '김가루 등을 올려서 함께 먹으면 더욱 맛있습니다.',
        ]
    },
    'cook_result4': {
        'name': '두부 스테이크',
        'image': 'images/dubu.jpg',
        'ingredients': [
            '두부 1모 (300g)',
            '양파 1/2개 (다져서 준비)',
            '달걀 1개',
            '빵가루 3T',
            '간장 2T',
            '소금과 후추 약간',
            '올리브유 2T',
        ],
        'instructions': [
            '두부를 으깨고 키친타월로 물기를 제거합니다.',
            '다진 양파, 달걀, 빵가루, 소금과 후추를 두부에 넣고 섞어줍니다.',
            '반죽을 스테이크 모양으로 성형합니다.',
            '팬에 올리브유를 두르고 중약불에서 두부 스테이크를 노릇하게 구워줍니다.',
            '간장과 물을 1:1 비율로 섞어 간장 소스를 만듭니다.',
            '완성된 두부 스테이크 위에 간장 소스를 뿌려 마무리합니다.',
        ],
        'tips': [
            '더 담백하게 즐기고 싶다면 간장 소스 대신 레몬즙을 곁들여 보세요.',
            '채식주의자는 달걀을 생략하고 아마씨 가루를 대체제로 사용할 수 있습니다.',
            '샐러드와 곁들이면 더욱 풍성한 한 끼가 됩니다.',
        ]
    },
    'cook_result5': {
        'name': '무채 된장 두부국',
        'image': 'images/mu_dwenjang_tofu_soup.jpg',
        'ingredients': [
            '무 100g (채 썰기, 당류: 1.8g)',
            '두부 1/2모 (당류: 0.5g)',
            '대파 약간 (당류: 0.5g)',
            '된장 1T (약 1g)',
            '물 500ml',
        ],
        'instructions': [
            '냄비에 물을 넣고 중불에서 끓인 후, 된장을 풀어줍니다.',
            '채 썬 무를 넣고 부드러워질 때까지 끓입니다.',
            '두부를 먹기 좋은 크기로 썰어 넣고 한소끔 더 끓입니다.',
            '대파를 넣고 소금으로 간을 맞춘 후 불을 끄고 완성합니다.',
        ],
        'tips': [
            '무와 된장이 만나 국물에 깊은 맛을 더해줍니다.',
            '기호에 따라 다진 마늘을 추가하면 더욱 풍미가 좋습니다.',
        ]
    },
    'cook_result6': {
        'name': '땅콩 없는 마가렛트 쿠키',
        'image': 'images/margaret_style_cookie.jpg',
        'ingredients': [
            '버터 100g (실온에서 부드럽게)',
            '설탕 50g',
            '달걀 1개',
            '아몬드 가루 또는 해바라기 씨 가루 30g',
            '밀가루 150g',
            '베이킹 파우더 1/2t',
            '소금 약간',
        ],
        'instructions': [
            '버터와 설탕을 넣고 부드럽게 크림화합니다.',
            '달걀을 넣어 잘 섞은 뒤, 아몬드 가루나 해바라기 씨 가루를 넣고 혼합합니다.',
            '밀가루, 베이킹 파우더, 소금을 넣고 반죽을 만듭니다.',
            '반죽을 작은 공 모양으로 만들어 팬에 올리고, 손으로 살짝 눌러 편평하게 합니다.',
            '170℃로 예열한 오븐에서 12-15분간 구워 완성합니다.',
        ],
        'tips': [
            '더 고소한 맛을 원하면 반죽에 약간의 바닐라 추출물을 추가해보세요.',
            '아몬드 가루 대신 해바라기 씨 가루를 사용해도 고소한 풍미를 살릴 수 있습니다.',
        ]
    },
}

@login_required
def cook_result(request):
    recipe = RECIPES_DATA.get('cook_result')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result1(request):
    recipe = RECIPES_DATA.get('cook_result1')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result2(request):
    recipe = RECIPES_DATA.get('cook_result2')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result3(request):
    recipe = RECIPES_DATA.get('cook_result3')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result4(request):
    recipe = RECIPES_DATA.get('cook_result4')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result5(request):
    recipe = RECIPES_DATA.get('cook_result5')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def cook_result6(request):
    recipe = RECIPES_DATA.get('cook_result6')
    return render(request, 'cook_result_generic.html', {'recipe': recipe})


@login_required
def allergy(request):
    recipe = RECIPES_DATA.get('cook_result') # Assuming cook_result is a generic recipe for allergy
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def low_calorie(request):
    recipe = RECIPES_DATA.get('cook_result4') # Assuming cook_result4 is low calorie
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

@login_required
def low_income(request):
    recipe = RECIPES_DATA.get('cook_result1') # Assuming cook_result1 is low income
    return render(request, 'cook_result_generic.html', {'recipe': recipe})

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
@login_required
def manual_input(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.user = request.user
            food_item.save()
            return redirect('manual_result')
    else:
        form = FoodItemForm()

    return render(request, 'manual_input.html', {'form': form})


@login_required
def manual_result(request):
    #food_items = FoodItem.objects.all().order_by('-created_at')
    food_items = FoodItem.objects.filter(user=request.user)
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

@login_required
def note_view(request):
    notes = Note.objects.filter(user=request.user)
    form = NoteForm()
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
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

@login_required
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
            file_path = os.path.join(settings.BASE_DIR, 'interface', 'static', 'community', file_name)
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
    drawing_images = os.listdir(os.path.join(settings.BASE_DIR, 'interface', 'static', 'community'))
    drawing_images = [f"community/{img}" for img in drawing_images]

    context = {
        'drawing_images': drawing_images,
    }
    return render(request, 'community.html', context)