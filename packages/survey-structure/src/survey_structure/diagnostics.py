"""Localized validation messages (port of ``validation-diagnostics.ts``)."""

from __future__ import annotations

from typing import Any

from survey_structure._js import UNDEFINED, to_string

# Semantic reasons: (English, Spanish).
_MESSAGES: dict[str, tuple[str, str]] = {
    "duplicate-group-id": (
        "The group id is duplicated.",
        "El identificador del grupo está duplicado.",
    ),
    "duplicate-response-key": (
        "The response key is produced more than once and would overwrite an answer.",
        "La clave de respuesta se genera más de una vez y sobrescribiría una respuesta.",
    ),
    "duplicate-field-id": (
        "The field id is duplicated.",
        "El identificador de la pregunta está duplicado.",
    ),
    "duplicate-field-code": (
        "The field code is duplicated.",
        "El código de la pregunta está duplicado.",
    ),
    "field-group-reference-missing": (
        "The field references a group that does not exist.",
        "La pregunta hace referencia a un grupo que no existe.",
    ),
    "top-level-field-has-parent": (
        "A top-level field cannot declare a parent.",
        "Una pregunta de primer nivel no puede declarar una pregunta padre.",
    ),
    "child-parent-reference-mismatch": (
        "The parent id does not match the containing field.",
        "El identificador de la pregunta padre no coincide con el contenedor.",
    ),
    "duplicate-subquestion-id": (
        "The subquestion id is duplicated.",
        "El identificador de la subpregunta está duplicado.",
    ),
    "duplicate-response-item-code": (
        "The response item code is duplicated within the field.",
        "El código del elemento de respuesta está duplicado dentro de la pregunta.",
    ),
    "condition-reference-missing-field": (
        "The condition references a field that does not exist.",
        "La condición hace referencia a una pregunta que no existe.",
    ),
    "condition-reference-missing-response-item": (
        "The condition references a response item that the field does not produce.",
        "La condición hace referencia a un elemento de respuesta que la pregunta no genera.",
    ),
    "duplicate-aggregate-response-item-code": (
        "An aggregate cannot include the same response item more than once.",
        "Una agregación no puede incluir el mismo elemento de respuesta más de una vez.",
    ),
    "comparison-requires-scalar-response": (
        "A comparison requires one scalar response, not a collection or display field.",
        "Una comparación requiere una respuesta escalar, no una colección ni un elemento informativo.",
    ),
    "pattern-requires-text-response": (
        "A pattern condition requires one text response.",
        "La condición con patrón requiere una respuesta de texto.",
    ),
    "numeric-bound-reference-incompatible": (
        "A numeric limit must reference an existing numeric question.",
        "El límite numérico debe consultar una pregunta numérica existente.",
    ),
    "comparison-value-type-mismatch": (
        "The comparison value does not match the response type or its declared options.",
        "El valor de comparación no coincide con el tipo de respuesta ni con sus opciones declaradas.",
    ),
    "selection-count-incompatible-field-type": (
        "Selection-count requires a field with multiple selected responses.",
        "El conteo de selecciones requiere una pregunta que permita varias respuestas seleccionadas.",
    ),
    "answered-count-incompatible-field-type": (
        "Answered-count requires multiple inputs or matrix response cells.",
        "El conteo de respuestas requiere varias entradas o celdas de respuesta de una matriz.",
    ),
    "count-requires-whole-field": (
        "A count refers to the entire question, not an individual response item.",
        "Un conteo hace referencia a la pregunta completa, no a un elemento de respuesta individual.",
    ),
    "numeric-aggregate-incompatible-field-type": (
        "A numeric aggregation requires numeric matrix cells.",
        "Una agregación numérica requiere celdas numéricas de una matriz.",
    ),
    "aggregate-requires-whole-field": (
        "An aggregate identifies its question with responseReference and its subset with responseItemCodes.",
        "Una agregación identifica su pregunta con responseReference y su subconjunto con responseItemCodes.",
    ),
    "ordered-comparison-incompatible-field-type": (
        "The response type is not compatible with an ordered comparison.",
        "El tipo de respuesta no es compatible con una comparación de orden.",
    ),
    "widget-not-compatible-with-field-type": (
        "The widget is not compatible with the field type.",
        "El componente visual no es compatible con el tipo de pregunta.",
    ),
    "other-option-code-collision": (
        "The other-response code duplicates an option code.",
        "El código de la respuesta «Otro» coincide con el código de una opción.",
    ),
    "other-comment-key-incompatible-field-type": (
        "An other-response comment key is not supported by this field type.",
        "Este tipo de pregunta no admite una clave de comentario para la respuesta «Otro».",
    ),
    "other-response-incompatible-field-type": (
        "This field type does not support an other response.",
        "Este tipo de pregunta no admite la respuesta «Otro».",
    ),
    "date-default-value-format-mismatch": (
        "The default date does not match its declared date format.",
        "La fecha predeterminada no coincide con el formato de fecha declarado.",
    ),
    "response-encoding-incompatible-field-type": (
        "This field type does not support selected/unselected response encoding.",
        "Este tipo de pregunta no admite una codificación de respuesta seleccionada/no seleccionada.",
    ),
    "response-encoding-value-type-mismatch": (
        "The encoded response values do not match the field type.",
        "Los valores de respuesta codificados no coinciden con el tipo de pregunta.",
    ),
    "response-encoding-label-pair-incomplete": (
        "Selected and unselected labels must be declared together.",
        "Las etiquetas de selección y no selección deben declararse juntas.",
    ),
    "default-value-validation-mismatch": (
        "The default value does not satisfy the declared validation rules.",
        "El valor predeterminado no cumple las reglas de validación declaradas.",
    ),
    "duplicate-default-option-code": (
        "The default value contains a duplicated option code.",
        "El valor predeterminado contiene un código de opción duplicado.",
    ),
    "ranking-default-not-a-complete-order": (
        "The default ranking must contain every option exactly once.",
        "El orden predeterminado debe contener cada opción exactamente una vez.",
    ),
    "default-value-reference-missing": (
        "The default value references an option or response item that does not exist.",
        "El valor predeterminado hace referencia a una opción o elemento de respuesta que no existe.",
    ),
    "validation-rule-not-applicable": (
        "The validation rule is not applicable to this field type.",
        "La regla de validación no se aplica a este tipo de pregunta.",
    ),
    "invalid-validation-pattern": (
        "The validation pattern must be a valid ECMAScript regular expression without flags.",
        "El patrón de validación debe ser una expresión regular válida de ECMAScript sin indicadores.",
    ),
}

# Zod structural codes: (English, Spanish).
_STRUCTURAL: dict[str, tuple[str, str]] = {
    "invalid_type": ("The value has an invalid type.", "El valor tiene un tipo no válido."),
    "invalid_literal": (
        "The value does not match the required literal.",
        "El valor no coincide con el literal requerido.",
    ),
    "invalid_union": (
        "The value does not match any supported variant.",
        "El valor no coincide con ninguna variante admitida.",
    ),
    "invalid_union_discriminator": (
        "The variant discriminator is invalid.",
        "El discriminador de la variante no es válido.",
    ),
    "invalid_enum_value": (
        "The value is not one of the allowed options.",
        "El valor no es una de las opciones permitidas.",
    ),
    "unrecognized_keys": (
        "The object contains unknown properties.",
        "El objeto contiene propiedades desconocidas.",
    ),
    "invalid_arguments": (
        "The function arguments are invalid.",
        "Los argumentos de la función no son válidos.",
    ),
    "invalid_return_type": (
        "The function return type is invalid.",
        "El tipo de retorno de la función no es válido.",
    ),
    "invalid_date": ("The date is invalid.", "La fecha no es válida."),
    "invalid_string": (
        "The text does not match the required format.",
        "El texto no cumple el formato requerido.",
    ),
    "too_small": (
        "The value is below the allowed minimum.",
        "El valor es inferior al mínimo permitido.",
    ),
    "too_big": ("The value exceeds the allowed maximum.", "El valor supera el máximo permitido."),
    "invalid_intersection_types": (
        "The validated variants cannot be merged.",
        "No se pueden combinar las variantes validadas.",
    ),
    "not_multiple_of": (
        "The value is not a multiple of the required number.",
        "El valor no es múltiplo del número requerido.",
    ),
    "not_finite": ("The number must be finite.", "El número debe ser finito."),
}


def resolve_survey_diagnostic_locale(locale: object) -> str:
    """Display language for diagnostics: ``es`` for any Spanish tag, otherwise ``en``."""
    if isinstance(locale, str):
        value = locale.strip().lower()
        if value == "es" or value.startswith(("es-", "es_")):
            return "es"
    return "en"


def localize_survey_validation_issue(issue: dict[str, Any], locale: object) -> str:
    """Localize known reasons; unknown diagnostics keep their original text."""
    params = issue.get("params") or {}
    reason = params.get("reason")
    spanish = resolve_survey_diagnostic_locale(locale) == "es"
    if not isinstance(reason, str) or reason not in _MESSAGES:
        if not spanish or issue["code"] not in _STRUCTURAL:
            return str(issue["message"])
        if issue["code"] == "invalid_type" and issue.get("received") == "undefined":
            return "El valor es obligatorio."
        message = _STRUCTURAL[issue["code"]][1]
        detail = UNDEFINED
        for key in ("keys", "expected", "minimum", "maximum"):
            value = issue.get(key, UNDEFINED)
            if value is not UNDEFINED and value is not None:
                detail = ", ".join(value) if key == "keys" else value
                break
        return message if detail is UNDEFINED else f"{message} ({to_string(detail)})"
    if reason == "condition-reference-missing-field":
        owner, field_code = params.get("owner"), params.get("fieldCode")
        if isinstance(owner, str) and owner and isinstance(field_code, str) and field_code:
            if spanish:
                if owner.startswith("field "):
                    owner = "la pregunta " + owner.removeprefix("field ")
                elif owner.startswith("group "):
                    owner = "el grupo " + owner.removeprefix("group ")
                return (
                    f"La condición de visibilidad de {owner} hace referencia al código de pregunta "
                    f'"{field_code}", pero no existe ninguna pregunta con ese código en la encuesta normalizada.'
                )
            return (
                f"The visibility condition of {owner} cannot be evaluated because it references field code "
                f'"{field_code}", but no field with that code exists in the normalized survey.'
            )
    message = _MESSAGES[reason][1 if spanish else 0]
    field_code = params.get("fieldCode")
    return f"{message} ({field_code})" if isinstance(field_code, str) else message
