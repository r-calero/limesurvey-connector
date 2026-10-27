# survey-data-dictionary (Python)

[English](README.md) | Español

Port en Python de [survey-data-dictionary](https://github.com/JJKid/survey-data-dictionary). Convierte una `SurveyStructure` en un diccionario de datos (columnas de respuesta, valores permitidos y alias), lo exporta a CSV y lo usa para traducir registros de respuesta o datos tabulares. Los resultados coinciden con el paquete TypeScript.

Solo depende de [survey-structure](../survey-structure) (el port en Python del contrato).

## Origen y versiones

| Versión Python | Versión npm que reproduce | `surveyStructureVersion` |
| --- | --- | --- |
| `2.1.0` | `survey-data-dictionary@2.1.0` (commit `99b1bd1`) | `2.1.0` |

La versión de Python sigue a la versión npm que reproduce; los arreglos solo de Python son post-releases. `survey_data_dictionary.UPSTREAM` registra la versión y el commit de npm. La paridad se comprueba en [limesurvey-connector](https://github.com/r-calero/limesurvey-connector) contra resultados producidos por el paquete TypeScript.

## Uso

```python
from survey_data_dictionary import build_survey_dictionary, dictionary_to_csv, translate_dataset

dictionary = build_survey_dictionary(structure, aliases={"external_consent": "Q1"})
csv_text = dictionary_to_csv(dictionary)
translated = translate_dataset(dictionary, [{"Q1": "A1"}], response_ids=["r-1"])
```

- `build_survey_dictionary(structure, *, aliases, source_issues, strict)`: valida primero la encuesta y lanza `SurveyStructureValidationError` si no es válida.
- `get_question_dictionary(dictionary, code)`: entradas de una pregunta.
- `translate_response` / `translate_dataset`: los valores conservan `sourceValue` y ganan `displayValue`; las claves desconocidas se conservan en `unmappedValues`.
- `map_tabular_dataset(dictionary, headers, rows, ...)`: alinea filas por posición sin fusionar encabezados repetidos.
- `dictionary_to_csv`, `translated_dataset_to_csv`: CSV con fórmulas de hoja de cálculo neutralizadas.
- `safe_parse_survey_dictionary`, `safe_parse_survey_response_dataset`: validación en tiempo de ejecución de diccionarios y datasets recibidos de otro sistema.

`ABSENT` marca un valor opcional omitido (`undefined` en JavaScript); `None` es `null` en JSON.

## Licencia

MIT. El paquete TypeScript original es de los autores de survey-data-dictionary; ver su repositorio.
