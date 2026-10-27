# limesurvey-connector

[English](README.md) | Español

Paquete de Python para trabajar con cuestionarios de LimeSurvey:

- `SurveyStructure`: contrato de cuestionario independiente de la fuente (versión 2.1.0), con validación y diagnósticos en español e inglés.
- Diccionarios de datos en JSON y CSV, y traducción de conjuntos de respuestas.
- Importación de archivos `.lss` y normalización de cuestionarios de LimeSurvey, sin servidor.
- Cliente de LimeSurvey RemoteControl 2.
- Servicio REST opcional construido con FastAPI.

> **Estado:** pre-alfa. Todas las funciones están implementadas y verificadas contra las implementaciones de referencia; aún no se han probado contra un servidor LimeSurvey en producción.

## Instalación

```bash
pip install limesurvey-connector            # librería, incluido el acceso por RemoteControl 2
pip install "limesurvey-connector[api]"     # servicio REST (FastAPI, Redis, JWT)
pip install "limesurvey-connector[pandas]"  # utilidades para DataFrames
```

Requiere Python 3.12 o posterior.

## Validar una SurveyStructure

El contrato se publica por separado como [`survey-structure`](packages/survey-structure), un port en Python del paquete TypeScript sin dependencias; `limesurvey_connector.survey_structure` lo reexporta.

```python
from limesurvey_connector.survey_structure import safe_parse_survey_structure

result = safe_parse_survey_structure(document)
if not result.success:
    for issue in result.issues:
        print(issue["path"], issue["message"])
```

`parse_survey_structure` devuelve el documento validado o lanza `SurveyStructureValidationError`. Los errores tienen el mismo `path`, `code`, `params` y `message` que el paquete TypeScript, así que un front que use `survey-structure` obtiene los mismos diagnósticos. `get_survey_execution_issues` indica lo que le falta a un borrador válido antes de publicarse.

`responseValidation.responseFormatPattern` es código ECMAScript que se evalúa tal como está escrito, con sus `patternFlags`; se traduce a una expresión `re` equivalente y se rechazan los pocos patrones que Python no puede evaluar igual ([detalle](conformance/known-divergences.json)).

## Diccionarios y respuestas

```python
from survey_data_dictionary import dictionary_to_csv
from limesurvey_connector.limesurvey import load_lss
from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.responses import translate_csv

loaded = load_lss("encuesta.lss")  # SurveyLoadResult
dictionary = build_limesurvey_dictionary(loaded["survey"], source_issues=loaded["issues"])
# Preguntas y columnas de sistema de LimeSurvey
codebook = dictionary_to_csv(
    build_limesurvey_dictionary(loaded["survey"], include_system_fields=True)
)
result = translate_csv(dictionary, export_text, format="vv", delimiter="\t")
```

Los diccionarios usan los nombres de columna de LimeSurvey con guion bajo (`Q1_SQ001`, `Q2_SQ001_0`, `Q11_SQ001comment`, `Q12_other`); las exportaciones con encabezados entre corchetes (`Q1[SQ001]`) se convierten al leerlas. En las exportaciones `vv`, `{question_not_shown}` se traduce como valor ausente. `includeTimingFields` añade `interviewtime`, `groupTime<id>` y `<código>Time`.

La lógica del diccionario se publica por separado como [`survey-data-dictionary`](packages/survey-data-dictionary). `translate_csv` lee las exportaciones de LimeSurvey igual que la API de referencia y conserva todas las columnas: las de sistema, como `submitdate` o `lastpage`, se traducen como campos con tipo, y solo se descartan los encabezados indicados en `ignored_headers`.

## LimeSurvey RemoteControl 2

```python
from limesurvey_connector.remote import LimeSurveyClient

with LimeSurveyClient(url, username, password, allowed_hosts=["encuestas.example.org"]) as ls:
    surveys = ls.list_surveys()
    dictionary = ls.get_dictionary(783587, language="es", include_system_fields=True)
    variable = ls.get_field(783587, "Q01", language="es")
    responses = ls.export_responses(783587, completion_status="complete")
```

Los errores son subclases de `LimeSurveyError` con un `code` estable (`LS_SESSION_EXPIRED`, `LS_UNREACHABLE`, ...).

## Servicio REST

```bash
cp .env.example .env   # completa los secretos
docker compose up --build -d
```

La imagen instala la versión de PyPI indicada en `CONNECTOR_PYPI_VERSION`; déjala vacía para construir el código del checkout.

Swagger está en `/docs`. Autenticación (ADR 4):

1. `POST /v1/limesurvey/sessions` con `X-Api-Key` y `{url, username, password}` devuelve `accessToken`.
2. Las rutas de LimeSurvey usan `Authorization: Bearer <accessToken>`; `DELETE /v1/limesurvey/sessions/current` lo revoca.
3. Las rutas que no contactan LimeSurvey usan solo `X-Api-Key`.

| Ruta | Credencial |
| --- | --- |
| `GET /v1/limesurvey/surveys` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/structure` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/fields/{questionCode}` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/dictionary` (`format`, `questionCode`, `includeSystemFields`, `refresh`) | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/responses` (JSON o CSV original) | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/responses/translated` | Bearer |
| `POST /v1/survey-structure/validate`, `/v1/survey-structure/readiness` | API key |
| `POST /v1/dictionaries/generate`, `/v1/dictionaries/from-lss`, `/v1/survey-structures/from-lss` | API key |
| `POST /v1/responses/translate` (registros o CSV) | API key |
| `GET /v1/contract`, `/v1/compatibility` | API key |

Los mensajes siguen `Accept-Language` (es o en). La configuración está documentada en `.env.example`.

## Desarrollo

Requisitos: [uv](https://docs.astral.sh/uv/) y Node 22 para la suite de conformidad.

```bash
make sync        # crea el entorno con todos los paquetes y extras
make lint        # ruff
make typecheck   # mypy --strict
make test        # pytest
```

Ejecutar el servicio en local:

```bash
uv run uvicorn limesurvey_connector.api.app:create_app --factory --reload
curl http://127.0.0.1:8000/health
```

## Conformidad con las implementaciones de referencia

Este paquete reproduce el comportamiento de cuatro proyectos existentes:

| Proyecto | Lenguaje | Función |
| --- | --- | --- |
| [survey-structure](https://github.com/JJKid/survey-structure) | TypeScript | Contrato `SurveyStructure` |
| [survey-data-dictionary](https://github.com/JJKid/survey-data-dictionary) | TypeScript | Diccionarios y traducción |
| [limesurvey-rc2-api](https://github.com/JJKid/limesurvey-rc2-api) | Python | Acceso por RemoteControl 2 y normalización |
| [limesurvey-dictionary-api](https://github.com/JJKid/limesurvey-dictionary-api) | TypeScript | API REST pública |

Esos proyectos no se modifican. `conformance/sources.lock.json` fija el commit de cada uno y `conformance/goldens/` guarda los resultados que producen con las entradas de `conformance/fixtures/`. Las mejoras deliberadas respecto a las referencias se declaran en `conformance/intentional-changes.json`. Las pruebas comparan este paquete con esos resultados, y toda `SurveyStructure` que genere debe pasar además el validador TypeScript de `conformance/tools/`.

```bash
make goldens         # recompila las referencias en sus commits fijados y reescribe los goldens
make goldens-check   # falla si las referencias ya no producen los goldens guardados
```

Ambos comandos esperan los cuatro repositorios junto a este (`../survey-structure`, etc.). Se leen con `git archive` y las compilaciones se hacen en `conformance/.work/`, que git ignora. Con `SOURCES=remote` se clonan desde GitHub.

## Decisiones de diseño

Ver [docs/adr](docs/adr).

## Licencia

[MIT](LICENSE).
