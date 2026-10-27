FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
# Empty builds the wheels from this checkout; a version installs that release from PyPI.
ARG PYPI_VERSION=""
WORKDIR /src
COPY pyproject.toml uv.lock README.md README.es.md CHANGELOG.md LICENSE ./
COPY packages ./packages
COPY src ./src
RUN mkdir /wheels && if [ -n "$PYPI_VERSION" ]; then \
      echo "limesurvey-connector[api]==${PYPI_VERSION}" > /wheels/requirements.txt; \
    else \
      uv build --all-packages --wheel --out-dir /wheels \
      && echo "limesurvey-connector[api]==$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")" > /wheels/requirements.txt; \
    fi

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 --home-dir /app connector
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --find-links /wheels -r /wheels/requirements.txt && rm -rf /wheels
USER connector
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=4s --retries=6 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "limesurvey_connector.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
