from django import forms
from .models import FoodItem  # models.py에 정의된 FoodItem 모델을 임포트합니다.

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'purchase_date', 'expiry_date']
        labels = {
            'name': '음식 이름',
            'purchase_date': '구입 날짜',
            '`expiry_date`': '유통기한',
        }
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get("purchase_date")
        expiry_date = cleaned_data.get("expiry_date")

        if purchase_date and expiry_date:
            if expiry_date < purchase_date:
                self.add_error('expiry_date', '유통기한은 구입 날짜 이후여야 합니다.')

        return cleaned_data


from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'cols': 40, 'placeholder': '여기에 메모를 작성하세요...'})
        }
