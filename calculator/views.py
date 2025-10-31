"""ビュー定義。"""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .forms import BudgetForm
from meal_calculator import best_combination, fetch_menu, format_result


def index(request: HttpRequest) -> HttpResponse:
    """予算入力フォームと結果を表示するビュー。"""

    # 初期状態では空のフォームを用意
    context: dict[str, object] = {"form": BudgetForm()}

    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            # フォーム値を取り出し
            budget = form.cleaned_data["budget"]
            url = form.cleaned_data.get("url") or None
            output_format = form.cleaned_data["output_format"]

            try:
                items = fetch_menu(url or "https://west2-univ.jp/sp/menu.php?t=650111")
                total, combo = best_combination(items, budget)
            except SystemExit as exc:
                # fetch_menu内でのエラーはSystemExitで通知されるためメッセージを表示
                context = {"form": form, "error": str(exc)}
                return render(request, "calculator/index.html", context)

            if output_format == "json":
                # JSON形式を選択した場合はJsonResponseで返す
                payload = {
                    "total": total,
                    "items": [
                        {"name": item.name, "price": item.price}
                        for item in combo
                    ],
                    "budget": budget,
                    "url": url or "https://west2-univ.jp/sp/menu.php?t=650111",
                }
                return JsonResponse(payload, json_dumps_params={"ensure_ascii": False, "indent": 2})

            # テキスト形式の場合はフォーマットした文字列を渡す
            context = {
                "form": form,
                "result": format_result(total, combo),
                "items": combo,
                "total": total,
            }
        else:
            # バリデーションエラー時のコンテキスト
            context = {"form": form}
    return render(request, "calculator/index.html", context)
