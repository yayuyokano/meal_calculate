"""入力フォーム定義。"""
from django import forms

from .cafeterias import cafeteria_choices


class BudgetForm(forms.Form):
    """予算入力フォーム。"""

    budget = forms.IntegerField(
        label="予算 (円)",
        min_value=0,
        help_text="0以上の整数を入力してください",
    )
    cafeteria = forms.ChoiceField(
        label="食堂",
        choices=(),
        help_text="対象の食堂を選択してください",
    )
    output_format = forms.ChoiceField(
        label="出力形式",
        choices=[("text", "テキスト"), ("json", "JSON")],
        initial="text",
        widget=forms.RadioSelect,
    )
    limit_primary = forms.BooleanField(
        label="主菜・麺類・丼・カレー・オーダー・ケバブ&ベジタリアンからは1品まで",
        required=False,
        help_text="これらのカテゴリから同時に複数選びません。",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = cafeteria_choices()
        self.fields["cafeteria"].choices = choices
        if choices and not self.data and not self.initial.get("cafeteria"):
            self.fields["cafeteria"].initial = choices[0][0]
