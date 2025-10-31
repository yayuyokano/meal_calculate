"""入力フォーム定義。"""
from django import forms


class BudgetForm(forms.Form):
    """予算入力フォーム。"""

    budget = forms.IntegerField(
        label="予算 (円)",
        min_value=0,
        help_text="0以上の整数を入力してください",
    )
    url = forms.URLField(
        label="メニューURL",
        initial="https://west2-univ.jp/sp/menu.php?t=650111",
        help_text="カスタムURLを指定する場合に入力してください",
        required=False,
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
