# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('main_home/', views.main_home, name='main_home'),
    path('add_food/', views.add_food, name='add_food'),
    path('recipes/', views.recipes, name='recipes'),
    path('best_before/', views.best_before, name='best_before'),
    path('community/', views.community, name='community'),
    path('', views.profile, name='profile'),

    path('receipt_loading/', views.receipt_loading, name='receipt_loading'),
    path('run_capture_and_process/', views.run_capture_and_process, name='run_capture_and_process'),
    path('receipt_result/', views.receipt_result, name='receipt_result'),

    path('barcode_loading/', views.barcode_loading, name='barcode_loading'),
    path('barcode_scan_process/', views.barcode_scan_process, name='barcode_scan_process'),
    path('barcode_result/<int:food_id>/', views.barcode_result, name='barcode_result'),

    path('ai_scan_loading/', views.ai_scan_loading, name='ai_scan_loading'),
    path('ai_scan_result/', views.ai_scan_result, name='ai_scan_result'),
    path('ai_scan/', views.ai_scan, name='ai_scan'),
    path('delete-food/<int:item_id>/', views.delete_food_item, name='delete_food_item'),


    

    path('cook_loading1/', views.cook_loading1, name='cook_loading1'),
    path('cook_loading2/', views.cook_loading2, name='cook_loading2'),
    path('cook_loading3/', views.cook_loading3, name='cook_loading3'),
    path('cook_loading4/', views.cook_loading4, name='cook_loading4'),
    path('cook_loading5/', views.cook_loading5, name='cook_loading5'),
    path('cook_loading6/', views.cook_loading6, name='cook_loading6'),
    # path('cook_result/', views.cook_result, name='cook_result'),
    path('cook_result1/', views.cook_result1, name='cook_result1'),
    path('cook_result2/', views.cook_result2, name='cook_result2'),
    path('cook_result3/', views.cook_result3, name='cook_result3'),
    path('cook_result4/', views.cook_result4, name='cook_result4'),
    path('cook_result5/', views.cook_result5, name='cook_result5'),
    path('cook_result6/', views.cook_result6, name='cook_result6'),

    path('allergy/', views.allergy, name='allergy'),
    path('low_calorie/', views.low_calorie, name='low_calorie'),
    path('low_income', views.low_income, name='low_income'),

    
    # path('open_camera_1/', views.open_camera_1, name='open_camera_1'),  # 첫 번째 경로
    # path('open_camera_2/', views.open_camera_2, name='open_camera_2'),  # 두 번째 경로
    # path('next_page_1/', views.next_page_1, name='next_page_1'),  # 첫 번째 페이지
    path('next_page_2/', views.next_page_2, name='next_page_2'),  # 두 번째 페이지
    path('next_page_1/<str:variable>/', views.ncook_result1, name='cook_result1'),
    path('next_page_2/<str:variable>/', views.ncook_result1, name='cook_result1'),

    path('test/', views.test, name='test'),



    path('choice/', views.choice, name='choice'),
    path('manual_input/', views.manual_input, name='manual_input'),
    path('manual_result/', views.manual_result, name='manual_result'),
    path('toggle-keyboard/', views.toggle_keyboard, name='toggle_keyboard'),

    path('note/', views.note_view, name='note_view'),
    path('drawing/', views.drawing_page, name='drawing_page'),
    path('save_drawing/', views.save_drawing, name='save_drawing'),




]
