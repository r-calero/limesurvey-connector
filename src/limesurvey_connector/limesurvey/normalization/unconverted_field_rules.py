"""Report verified native behavior that the portable form does not execute."""

import os
from typing import Any

from .source_values import _issue, _optional_number, _record, _text, _yes
from .text_sanitizer import contains_embedded_javascript

# Printing, SPSS and statistics settings do not restrict an individual answer.
# Preserve them in the source details without classifying the question as partial.
SOURCE_ONLY_ATTRIBUTES = frozenset(
    {
        "page_break",
        "scale_export",
        "statistics_showgraph",
        "statistics_showmap",
        "statistics_graphtype",
        "public_statistics",
    }
)


def report_unconverted_field_rules(
    field: dict[str, Any],
    question: dict[str, Any],
    attributes: dict[str, Any],
    issues: list[dict[str, Any]],
    converted_rules: set[str] | None = None,
) -> dict[str, Any]:
    """Preserve exact source attributes, without guessing an equivalent rule."""
    native_type = field["source"]["nativeType"]
    code, qid = field["code"], field["source"].get("questionId", field["id"])
    originals: dict[str, Any] = {}
    spanish = os.environ.get("APP_LOCALE", "es").lower().startswith("es")

    def report(
        rule: str, value: Any, es: str, en: str, *, visibility: bool = False, source_key: str = ""
    ) -> None:
        originals[source_key or rule] = value
        details = (
            {"rule": rule, "sourceExpression": _text(value), "scope": "field"}
            if visibility
            else {"rule": rule, "sourceValue": value}
        )
        message = (
            f"La regla {rule} de {code} no se ejecuta: {es}"
            if spanish
            else f"Rule {rule} on {code} is not enforced: {en}"
        )
        issues.append(
            _issue(
                "warning",
                (
                    "SOURCE_SCRIPT_NOT_EXECUTED"
                    if rule == "embedded_javascript"
                    else "UNSUPPORTED_SOURCE_EXPRESSION"
                )
                if visibility
                else ("UNSUPPORTED_TIMER" if rule == "time_limit" else "INVALID_VALIDATION"),
                message,
                field_id=qid,
                question_code=code,
                details=details,
            )
        )

    # Applicability is documented in LimeSurvey questionHelper.php and the
    # corresponding qanda/em_manager helpers; presentation-only settings are not validation.
    if native_type == "D":
        for rule, portable, es, en in (
            ("date_min", "dateMin", "el límite de fecha mínima", "the minimum date bound"),
            ("date_max", "dateMax", "el límite de fecha máxima", "the maximum date bound"),
        ):
            if (
                _text(attributes.get(rule)).strip()
                and portable not in field.get("responseValidation", {})
                and f"{portable}Reference" not in field.get("responseValidation", {})
            ):
                report(
                    rule,
                    attributes[rule],
                    es + " sólo se conserva en el origen.",
                    en + " is retained only in the source.",
                )
    maximum_chars = _optional_number(attributes.get("maximum_chars"))
    if (
        native_type in {"N", "S", "T", "U", "Q", "K", ";"}
        and maximum_chars is not None
        and maximum_chars > 0
        and field.get("responseValidation", {}).get("maxLength") != maximum_chars
    ):
        report(
            "maximum_chars",
            attributes["maximum_chars"],
            "el máximo de caracteres no limita la respuesta; no equivale a un máximo numérico.",
            "the character limit does not restrict the answer; it is not a numeric maximum.",
        )
    if (
        native_type in {"S", "Q", ";"}
        and _yes(attributes.get("numbers_only"))
        and not field.get("responseValidation", {}).get("numericText")
    ):
        report(
            "numbers_only",
            attributes["numbers_only"],
            "el campo de texto permite también respuestas no numéricas.",
            "the text input also accepts nonnumeric answers.",
        )
    pattern = _record(question.get("result")).get("preg", question.get("preg"))
    if (
        native_type in {"N", "S", "T", "U", "Q", "K", ";", ":"}
        and _text(pattern).strip()
        and "responseFormatPattern" not in field.get("responseValidation", {})
    ):
        report(
            "preg",
            pattern,
            (
                "la respuesta numérica no conserva el texto exacto escrito que necesita esta expresión regular."
                if native_type == "N"
                else "esta expresión regular no se pudo convertir para este tipo de respuesta."
            ),
            (
                "the numeric response does not preserve the exact input text required by this regular expression."
                if native_type == "N"
                else "this regular expression could not be converted for this response type."
            ),
        )
    if (
        native_type in {"S", "T", "U", "X", "L", "!"}
        and (_optional_number(attributes.get("time_limit")) or 0) > 0
    ):
        report(
            "time_limit",
            attributes["time_limit"],
            "no hay temporizador ni se ejecutan sus acciones o bloqueos de navegación.",
            "there is no timer and its actions or navigation locks are not executed.",
        )
        originals.update(
            {
                key: value
                for key, value in attributes.items()
                if key.startswith("time_limit_") and _text(value).strip()
            }
        )
    if native_type == "K":
        for rule, portable in (
            ("min_num_value_n", "itemMin"),
            ("max_num_value_n", "itemMax"),
            ("min_num_value", "sumMin"),
            ("max_num_value", "sumMax"),
            ("equals_num_value", "sumEquals"),
        ):
            if _text(attributes.get(rule)).strip() and portable not in field.get(
                "responseValidation", {}
            ):
                report(
                    rule,
                    attributes[rule],
                    "se conservan las casillas numéricas, pero este límite o suma todavía no se comprueba.",
                    "numeric inputs remain available, but this bound or sum is not checked yet.",
                )
        if _yes(attributes.get("num_value_int_only")) and not field.get(
            "responseValidation", {}
        ).get("integer"):
            report(
                "num_value_int_only",
                attributes["num_value_int_only"],
                "se aceptan números decimales aunque LimeSurvey sólo acepta enteros.",
                "decimal numbers are accepted although LimeSurvey requires integers.",
            )
        if _yes(attributes.get("slider_layout")):
            report(
                "slider_layout",
                attributes["slider_layout"],
                "se muestran casillas numéricas en lugar de los controles deslizantes originales.",
                "numeric text boxes appear instead of the original sliders.",
            )
            originals.update(
                {
                    key: value
                    for key, value in attributes.items()
                    if key.startswith("slider_") and _text(value).strip()
                }
            )
    if _yes(attributes.get("hidden")) and not field.get("rendering", {}).get("hidden"):
        report(
            "hidden",
            attributes["hidden"],
            "la ocultación permanente no se aplica; la pregunta puede mostrarse si su relevancia lo permite.",
            "permanent hiding is not applied; the question may be shown when its relevance allows it.",
            visibility=True,
        )
    capacity = _optional_number(attributes.get("max_subquestions"))
    if native_type == "R" and capacity is not None and 0 < capacity < len(field.get("options", [])):
        portable_max = field.get("responseValidation", {}).get("maxSelections")
        if portable_max is None or portable_max > capacity:
            report(
                "max_subquestions",
                attributes["max_subquestions"],
                "el número máximo de posiciones del ranking no se limita como en el origen.",
                "the maximum number of ranking positions is not restricted as in the source.",
            )
    if (
        native_type in {"L", "!", "P"}
        and field.get("other")
        and field.get("required")
        and _yes(attributes.get("other_comment_mandatory"))
        and not field["other"].get("commentRequired" if native_type == "P" else "textRequired")
    ):
        report(
            "other_comment_mandatory",
            attributes["other_comment_mandatory"],
            "el texto o comentario de Otro no se exige al seleccionar esa opción.",
            "the Other text or comment is not required when that option is selected.",
        )
    for rule, effect in (
        ("array_filter", "filtra las subpreguntas según otra respuesta"),
        ("array_filter_style", "usa filas deshabilitadas en lugar de ocultarlas"),
        ("exclude_all_others_auto", "selecciona automáticamente la opción excluyente"),
        ("autocheck_exclusive_option", "selecciona automáticamente la opción excluyente"),
        ("array_filter_exclude", "excluye subpreguntas según otra respuesta"),
        ("random_group", "mezcla el orden de las preguntas del grupo aleatorio"),
        ("random_order", "mezcla el orden de opciones o subpreguntas"),
        (
            "exclusive_option",
            "desmarca y bloquea las demás opciones al elegir una opción exclusiva",
        ),
        ("exclude_all_others", "desmarca las demás opciones al elegir una opción exclusiva"),
        ("assessment_value", "contribuye a una calificación que el visor no calcula"),
        ("other_numbers_only", "exige números en el texto de Otro"),
        ("answer_order", "cambia el orden de las opciones"),
        ("subquestion_order", "cambia el orden de las subpreguntas"),
    ):
        value = attributes.get(rule)
        if rule in (converted_rules or set()):
            continue
        if (
            not _text(value).strip()
            or (rule == "array_filter_style" and _text(value).strip() == "0")
            or (
                rule in {"autocheck_exclusive_option", "exclude_all_others_auto"}
                and not _yes(value)
            )
            or (rule in {"random_order", "other_numbers_only"} and not _yes(value))
            or (
                rule in {"exclusive_option", "exclude_all_others"}
                and _text(value).strip().upper() in {"0", "N"}
            )
            or (rule == "assessment_value" and _optional_number(value) == 0)
            or (
                rule in {"answer_order", "subquestion_order"}
                and _text(value).strip().lower() == "normal"
            )
        ):
            continue
        originals[rule] = value
        issues.append(
            _issue(
                "warning",
                "INVALID_VALIDATION",
                (
                    f"La regla {rule} de {code} no se ejecuta: {effect}."
                    if spanish
                    else f"Rule {rule} on {code} is not executed by the portable renderer."
                ),
                field_id=qid,
                question_code=code,
                details={"rule": rule, "sourceValue": value},
            )
        )
    # Known source settings remain handled or diagnosed above. Preserve any
    # additional property explicitly so a future setting cannot disappear silently.
    known = set(
        [
            "array_filter_style",
            "autocheck_exclusive_option",
            "exclude_all_others_auto",
            "hidden",
            "date_time_format",
            "date_min",
            "date_max",
            "minimum_answer",
            "maximum_answer",
            "min_num_value",
            "max_num_value",
            "min_answers",
            "max_answers",
            "min_num_value_n",
            "max_num_value_n",
            "equals_num_value",
            "value_range_allows_missing",
            "num_value_int_only",
            "maximum_chars",
            "max_subquestions",
            "numbers_only",
            "preg",
            "em_validation_q",
            "em_validation_sq",
            "multiflexible_min",
            "multiflexible_max",
            "multiflexible_step",
            "multiflexible_checkbox",
            "dualscale_headerA",
            "dualscale_headerB",
            "other_comment_mandatory",
            "array_filter",
            "array_filter_exclude",
            "random_group",
            "random_order",
            "exclusive_option",
            "exclude_all_others",
            "assessment_value",
            "other_numbers_only",
            "answer_order",
            "subquestion_order",
            "time_limit",
            "time_limit_action",
            "time_limit_disable_next",
            "time_limit_disable_prev",
            "time_limit_message",
            "time_limit_message_style",
            "time_limit_warning",
            "time_limit_warning_message",
            "time_limit_warning_message_style",
            "hide_tip",
            "question_template",
            "answer_width",
            "subquestion_width",
            "display_columns",
            "prefix",
            "suffix",
            "css_class",
            "text_input_width",
            "label_input_columns",
            "input_boxes",
            "input_size",
            "dropdown",
            "dropdown_size",
            "dropdown_dates",
            "dropdown_dates_year_min",
            "dropdown_dates_year_max",
            "show_title",
            "show_totals",
            "show_grand_total",
            "show_row_totals",
            "show_column_totals",
            "slider_layout",
            "slider_min",
            "slider_max",
            "slider_step",
            "slider_default",
            "slider_accuracy",
            "slider_middlestart",
            "use_dropdown",
            "list_comment_size",
            "save_as_default_value",
            "hide_comment",
            "hide_answers",
            "location_mapservice",
            "location_mapwidth",
            "location_mapheight",
            "location_mapzoom",
        ]
    )
    for name, value in attributes.items():
        if name in (converted_rules or set()):
            continue
        if name in SOURCE_ONLY_ATTRIBUTES and _text(value).strip():
            originals[name] = value
            continue
        if name not in known and _text(value).strip():
            originals[name] = value
            diagnostic = (
                "UNSUPPORTED_TIMER_SETTING"
                if name.startswith("time_limit_")
                else "UNSUPPORTED_LOCATION_SETTING"
                if name.startswith("location_")
                else "UNCONVERTED_SOURCE_PROPERTY"
            )
            issues.append(
                _issue(
                    "warning",
                    diagnostic,
                    f"LimeSurvey envió la configuración {name}. Se conserva su valor para consulta.",
                    field_id=qid,
                    question_code=code,
                    details={"propertyName": name, "sourceValue": value},
                )
            )
    result = _record(question.get("result"))
    for property_name in ("question", "help"):
        html = question.get(property_name) or result.get(property_name)
        if contains_embedded_javascript(html):
            report(
                "embedded_javascript",
                html,
                f"el JavaScript incorporado en {property_name} se conserva como texto original para consulta, pero no se ejecuta. Sus validaciones, selecciones iniciales o interacciones no se reproducen.",
                f"JavaScript embedded in {property_name} is retained as original text for reference but is not executed. Its validations, initial selections or interactions are not reproduced.",
                visibility=True,
                source_key=property_name,
            )
    return originals
