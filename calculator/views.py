"""ビュー定義。"""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .cafeterias import cafeteria_name, cafeteria_url
from .forms import BudgetForm
from meal_calculator import best_combination, fetch_menu, format_result


def _expects_json(request: HttpRequest, form: BudgetForm) -> bool:
    """AJAX/JSONレスポンスが要求されているかを判定する。"""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return True
    accept = request.headers.get("accept", "")
    if "application/json" in accept.lower():
        return True
    return form.data.get("output_format") == "json"


def _serialize_form_errors(form: BudgetForm) -> dict[str, list[str]]:
    """フォームのエラーをJSONレスポンス用に整形する。"""
    errors: dict[str, list[str]] = {}
    for field, messages in form.errors.get_json_data().items():
        errors[field] = [entry.get("message", "") for entry in messages]
    return errors


def index(request: HttpRequest) -> HttpResponse:
    """予算入力フォームと結果を表示するビュー。"""

    form = BudgetForm(request.POST or None)
    context: dict[str, object] = {
        "form": form,
        "limit_primary_checked": bool(form["limit_primary"].value()),
        "selected_cafeteria": None,
    }
    current_cafeteria = form["cafeteria"].value()
    if current_cafeteria:
        context["selected_cafeteria"] = cafeteria_name(current_cafeteria)

    if request.method == "POST":
        expects_json = _expects_json(request, form)
        if form.is_valid():
            budget = form.cleaned_data["budget"]
            cafeteria_id = form.cleaned_data["cafeteria"]
            url = cafeteria_url(cafeteria_id)
            selected_cafeteria = cafeteria_name(cafeteria_id)
            output_format = form.cleaned_data["output_format"]
            limit_primary = form.cleaned_data["limit_primary"]
            use_playwright = True

            try:
                items = fetch_menu(url, use_playwright=use_playwright)
                total, combo = best_combination(items, budget, limit_primary=limit_primary)
            except SystemExit as exc:
                if expects_json or output_format == "json":
                    return JsonResponse(
                        {"error": str(exc)},
                        status=400,
                        json_dumps_params={"ensure_ascii": False},
                    )
                context.update(
                    {
                        "error": str(exc),
                        "limit_primary_checked": limit_primary,
                        "selected_cafeteria": selected_cafeteria,
                    }
                )
                return render(request, "calculator/index.html", context)

            payload = {
                "total": total,
                "items": [
                    {"name": item.name, "price": item.price, "category": item.category}
                    for item in combo
                ],
                "menu_items": [
                    {"name": item.name, "price": item.price, "category": item.category}
                    for item in items
                ],
                "budget": budget,
                "url": url,
                "cafeteria_id": cafeteria_id,
                "cafeteria_name": selected_cafeteria,
                "limit_primary": limit_primary,
                "use_playwright": use_playwright,
            }

            if expects_json or output_format == "json":
                json_kwargs: dict[str, object] = {"ensure_ascii": False}
                if output_format == "json":
                    json_kwargs["indent"] = 2
                return JsonResponse(payload, json_dumps_params=json_kwargs)

            context.update(
                {
                    "result": format_result(total, combo),
                    "items": combo,
                    "menu_items": items,
                    "total": total,
                    "limit_primary_checked": limit_primary,
                    "selected_cafeteria": selected_cafeteria,
                }
            )
        else:
            if expects_json:
                return JsonResponse(
                    {
                        "error": "入力内容を確認してください。",
                        "field_errors": _serialize_form_errors(form),
                    },
                    status=400,
                    json_dumps_params={"ensure_ascii": False},
                )
    return render(request, "calculator/index.html", context)
