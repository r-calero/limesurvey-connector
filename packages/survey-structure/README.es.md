# survey-structure (Python)

[English](README.md) | Español

Port en Python de [survey-structure](https://github.com/JJKid/survey-structure), el contrato TypeScript para definir cuestionarios de forma independiente de la fuente. Valida documentos `SurveyStructure` y `SurveyLoadResult` (SurveyStructure 2.1.0) y reporta los mismos errores que el paquete TypeScript: mismo `path`, `code`, `params` y `message`.

No tiene dependencias fuera de la biblioteca estándar de Python.

## Origen y versiones

| Versión Python | Versión npm que reproduce | `surveyStructureVersion` |
| --- | --- | --- |
| `2.1.0` | `survey-structure@2.1.0` (commit `0148e3f`) | `2.1.0` |

La versión de Python es la versión npm que reproduce, que desde 2.1.0 coincide con la del contrato. Un arreglo solo de Python se publica como post-release (`2.1.0.post1`). `survey_structure.UPSTREAM` registra la versión y el commit de npm.

La paridad se comprueba en [limesurvey-connector](https://github.com/r-calero/limesurvey-connector), donde el paquete TypeScript se compila en su commit fijado para producir los resultados esperados: 234 casos del contrato con sus mensajes en español e inglés, 73 etiquetas de idioma, 20 608 combinaciones de patrón, flags y valor, 107 URL de imágenes, y las funciones de calificación y de texto numérico. Todo documento que este paquete acepta también lo acepta el validador TypeScript.

`localize_survey_validation_issue(issue, locale)` da el texto en español o inglés de cualquier error, como `localizeSurveyValidationIssue`.

## Instalación

```bash
pip install survey-structure
```

Requiere Python 3.12 o posterior.

## Uso

```python
from survey_structure import parse_survey_structure, safe_parse_survey_structure

result = safe_parse_survey_structure(document)
if not result.success:
    for issue in result.issues:
        print(issue["path"], issue["code"], issue["message"])

survey = parse_survey_structure(document)  # lanza SurveyStructureValidationError
```

Otras funciones:

- `parse_survey_load_result` / `safe_parse_survey_load_result`: resultados de importación o carga.
- `get_survey_execution_issues(survey)`: lo que le falta a un borrador válido antes de publicarse.
- `field_response_keys(field)`: columnas de respuesta que produce una pregunta.
- `to_python_pattern(pattern, flags)` y `test_pattern(pattern, value, flags)`: usar un `responseFormatPattern` desde Python.
- `calculate_survey_score` y `grade_survey_answer`: calificación automática de respuestas normalizadas.
- `parse_survey_response_record`, `is_numeric_text`, `number_character_length`, `is_month_day`, `month_day_count` y `validation_pattern_source`.
- `FIELD_WIDGET_COMPATIBILITY`, `SURVEY_STRUCTURE_VERSION` y las definiciones `TypedDict` en `survey_structure.types`.

## Patrones

`responseFormatPattern` es código fuente ECMAScript que se evalúa tal como está escrito (sin anclas), y `patternFlags` puede contener `i`, `m` y `s`. El paquete traduce el patrón a una expresión `re` equivalente que se evalúa sobre unidades UTF-16, como hace ECMAScript, incluidas sus reglas de mayúsculas y minúsculas para `i` y sus terminadores de línea para `m`. Los patrones que Python no puede evaluar igual (lookbehind de longitud variable, una referencia dentro de un grupo repetido que contiene su captura, una referencia con `i`, nombres de grupo con `$`) se rechazan, de modo que todo patrón aceptado significa lo mismo en ambos lenguajes.

Las URL de imágenes se validan como lo hace `new URL()` (estándar WHATWG URL); los dominios internacionalizados usan el códec IDNA 2003 de Python, así que algunos hosts no ASCII poco comunes pueden evaluarse distinto.

## Licencia

MIT. El paquete TypeScript original es de los autores de survey-structure; ver su repositorio.
