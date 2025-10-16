# AI Refrigerator: IOMEAL

IOMEAL은 **라즈베리파이 5와 터치스크린**을 활용한 저비용 모듈형 스마트 냉장고 시스템입니다.
기존 냉장고나 팬트리에 부착하여, 식재료 관리·유통기한 추적·레시피 추천·가족 간 메모 공유를 가능하게 합니다.

---

## 프로젝트 개요

* **개인 맞춤형 프로필 관리:** 가족 구성원별 건강정보, 알레르기, 선호도를 반영하여 맞춤형 레시피를 제공합니다.
* **식재료 자동 등록:** 카메라 기반 AI 객체 인식으로 식재료를 자동 등록합니다.
* **OCR 및 바코드 인식:** 영수증 인식(OCR) 및 바코드 스캔을 통해 재료 정보를 빠르게 추가할 수 있습니다.
* **유통기한 추적 및 알림:** 등록된 식재료의 유통기한을 관리하고, 만료 임박 알림을 제공합니다.
* **AI 레시피 추천:** 보유 재료를 기반으로 OpenAI API를 활용해 최적의 레시피를 추천합니다.
* **가족 커뮤니티:** 냉장고 화면에서 메모나 그림을 남겨 가족 간 커뮤니케이션을 지원합니다.

---

## 기술 스택

| 구분         | 기술                                     |
| ---------- | -------------------------------------- |
| **하드웨어**   | Raspberry Pi 5, Touchscreen            |
| **백엔드**    | Python, Django                         |
| **프론트엔드**  | HTML, CSS, JavaScript                  |
| **AI/ML**  | OpenCV, Ultralytics (YOLO), OpenAI API |
| **데이터베이스** | SQLite (기본값)                           |

---

## 설치 및 실행 방법

1. **프로젝트 클론**

   ```bash
   git clone https://github.com/Kimjh01/AI_Refrigerator.git
   cd AI_Refrigerator
   ```

2. **가상환경 생성 및 활성화**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **필수 패키지 설치**

   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 파일(.env) 생성**
   프로젝트 루트에 `.env` 파일을 만들고 다음 내용을 추가합니다.

   ```env
   OPENAI_API_KEY="YOUR_OPENAI_KEY"
   SECRET_KEY="YOUR_DJANGO_SECRET"
   DEBUG=True
   ```

5. **데이터베이스 마이그레이션**

   ```bash
   python manage.py migrate
   ```

6. **관리자 계정 생성**

   ```bash
   python manage.py createsuperuser
   ```

7. **개발 서버 실행**

   ```bash
   python manage.py runserver
   ```

   실행 후 브라우저에서 `http://127.0.0.1:8000/` 접속

---

## 프로젝트 구조

```
AI_Refrigerator/
├── accounts/               # 사용자 인증 및 프로필 관리
│   ├── models.py
│   ├── views.py
│   └── templates/accounts/
│       ├── login.html
│       └── profile.html
│
├── interface/              # 주요 기능 (AI, 레시피, 인식 등)
│   ├── views.py
│   ├── camera.py
│   ├── scan.py
│   ├── receipt.py
│   ├── static/
│   │   └── best.pt         # YOLO 모델 가중치
│   └── templates/
│       ├── main_home.html
│       ├── recipes.html
│       └── ai_scan_result.html
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── media/                  # 사용자 업로드 파일
├── .env                    # 환경 변수 (생성 필요)
├── manage.py
└── requirements.txt
```

---

## 추가 참고사항

* `.env` 파일은 반드시 `.gitignore`에 포함해야 합니다.
* 현재 프로젝트는 **라즈베리파이 환경에서 구동 가능한 수준까지 구현된 개발용 버전**입니다.
* 배포(Deploy) 환경 설정은 포함되어 있지 않습니다. (개발 시 로컬 서버 기반 실행)

---
