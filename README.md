# AI Refrigerator

## 프로젝트 소개

AI Refrigerator는 라즈베리파이 5와 터치스크린을 활용한 저비용 모듈형 장치다. 기존의 일반 냉장고나 팬트리(식료품 저장소)에 부착하면, 이를 스마트 기기로 변환시켜 식재료를 효율적으로 관리할 수 있게 돕는다.

## 프로젝트 시연

[여기에 프로젝트의 실제 작동 모습을 담은 스크린샷이나 영상을 추가한다.]

## 주요 기능

*   **식재료 관리**: AI 객체 인식, 영수증 OCR, 바코드 스캔, 수동 입력을 통해 식재료를 등록하고 관리한다.
*   **유통기한 추적**: 등록된 식재료의 유통기한을 추적하고 알림을 보내 음식물 낭비를 줄인다.
*   **레시피 추천**: 보유한 식재료를 기반으로 AI가 최적의 레시피를 추천한다.
*   **커뮤니티**: 가족 구성원과 메모나 그림을 공유하는 소통 공간을 제공한다.
*   **사용자 프로필**: 개인의 건강 정보, 알러지 등을 등록하여 맞춤형 식단 관리를 지원한다.

## 기술 스택

*   **하드웨어**: Raspberry Pi 5, Touchscreen
*   **백엔드**: Python, Django
*   **프론트엔드**: HTML, CSS, JavaScript
*   **AI/ML**: OpenCV, Ultralytics (YOLO), OpenAI API
*   **데이터베이스**: SQLite (기본값)

## 설치 및 실행

1.  **프로젝트 클론**
    ```bash
    git clone https://github.com/your-username/AI_Refrigerator.git
    cd AI_Refrigerator
    ```

2.  **가상환경 생성 및 활성화**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **의존성 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API 키 설정**
    프로젝트 루트 디렉토리에 `.env` 파일을 생성한다. 자세한 내용은 아래 **API 키 설정** 섹션을 참고한다.

5.  **데이터베이스 마이그레이션**
    ```bash
    python manage.py migrate
    ```

6.  **관리자 계정 생성**
    ```bash
    python manage.py createsuperuser
    ```
    터미널의 안내에 따라 관리자 계정의 아이디, 이메일, 비밀번호를 설정한다.

7.  **개발 서버 실행**
    ```bash
    python manage.py runserver
    ```
    서버 실행 후 웹 브라우저에서 `http://127.0.0.1:8000/` 주소로 접속하여 애플리케이션을 확인한다.

## API 키 설정

AI 레시피 추천 기능은 OpenAI API를 사용하므로 API 키 설정이 필수적이다.

1.  [OpenAI Platform](https://platform.openai.com/)에서 API 키를 발급받는다.
2.  프로젝트 루트 디렉토리(`manage.py` 파일이 있는 위치)에 `.env` 파일을 생성한다.
3.  생성한 `.env` 파일에 아래 형식에 맞춰 키를 입력하고 저장한다.

    ```env
    # OpenAI API 키 (필수)
    # AI 레시피 추천 기능에 사용된다.
    OPENAI_API_KEY="*********************"

    # 다른 API 키가 필요한 경우 아래에 추가한다.
    # 예: BARCODE_API_KEY="*********************"
    ```

**참고**: `.env` 파일은 민감한 정보를 포함하므로, `.gitignore` 파일에 `.env`가 추가되어 있는지 확인하여 Git 저장소에 올라가지 않도록 주의한다.

## 프로젝트 구조

```
AI_Refrigerator/
├── accounts/               # 사용자 인증 및 프로필 관리 앱
│   ├── models.py           # User, Profile 모델 정의
│   ├── views.py            # 로그인, 로그아웃, 프로필 관련 뷰 로직
│   └── templates/accounts/ # 계정 관리용 HTML 템플릿
│       ├── login.html
│       └── profile.html
│
├── interface/              # AI 기능, 레시피 등 핵심 기능 앱
│   ├── views.py            # 식재료 관리, 레시피 추천 등 핵심 뷰 로직
│   ├── camera.py           # 카메라 제어 및 이미지 처리 모듈
│   ├── scan.py             # AI 객체 탐지(YOLO) 처리 모듈
│   ├── receipt.py          # 영수증 이미지 처리(OCR) 모듈
│   ├── static/
│   │   └── best.pt         # 학습된 커스텀 YOLO 모델 가중치 파일
│   └── templates/
│       ├── main_home.html  # 메인 페이지 템플릿
│       ├── recipes.html    # 레시피 추천 결과 템플릿
│       └── ai_scan_result.html # AI 스캔 결과 템플릿
│
├── config/                 # 프로젝트 전체 설정
│   ├── settings.py         # 메인 설정 (DB, API 키 연동, 앱 등록)
│   └── urls.py             # 최상위 URL 라우팅
│
├── media/                  # 사용자가 업로드하는 미디어 파일 (프로필 사진 등)
├── .env                    # (생성 필요) API 키 등 환경 변수 파일
├── manage.py               # Django 관리 스크립트
└── requirements.txt        # 의존성 패키지 목록
```