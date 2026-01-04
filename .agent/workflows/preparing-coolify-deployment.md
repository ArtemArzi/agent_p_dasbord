---
description: Prepares a Python project for deployment on a Coolify server. Analyzes Docker configuration, environment variables, and generates necessary production assets. Use when the user mentions "Coolify", "deploy", "production", or "server setup".
---

# Preparing for Coolify Deployment

## Overview
Превращает текущий проект в готовый к развертыванию артефакт для платформы Coolify. Этот навык анализирует существующую конфигурацию Docker, оптимизирует ее для продакшена и создает необходимые инструкции для настройки сервиса.

## When to use this skill

### Triggers
* Пользователь просит "подготовить проект к деплою".
* Упоминание настройки сервера Coolify или Docker Compose для продакшена.
* Запросы на проверку `Dockerfile` или `docker-compose.yml` перед релизом.
* Необходимость создания переменных окружения для продакшена.

### Anti-Triggers
* Локальная разработка или дебаггинг (использовать `debugging-python`).
* Деплой на Serverless (AWS Lambda, Vercel), если не используется Coolify как посредник.
* Написание бизнес-логики приложения.

## Objective & Boundaries

### Goal
Обеспечить успешный "zero-downtime" деплой приложения в Coolify, гарантируя корректную обработку портов, секретов и персистентности данных.

### Permissions
* **Чтение:** Все файлы конфигурации (`Dockerfile`, `*.yml`, `requirements.txt`, `.env.*`).
* **Запись:** Создание/обновление `docker-compose.prod.yml`, `coolify.yaml` (если применимо), `.env.production`.
* **Запрещено:** Деплоить напрямую на сервер (агент готовит файлы, пользователь нажимает кнопку в UI Coolify).

## Inputs
* Существующие `Dockerfile` и `docker-compose.yml` (если есть).
* `requirements.txt` или менеджер пакетов.
* Специфика приложения (Streamlit, FastAPI и т.д. — определяется автоматически).

## Outputs
* **Optimized Dockerfile:** Multi-stage build для минимизации размера образа.
* **Production Compose:** `docker-compose.prod.yml` с настроенными политиками рестарта и healthcheck-ами.
* **Env Template:** Список необходимых переменных окружения для панели Coolify.
* **Deployment Guide:** Краткая инструкция по настройке в UI Coolify (Domains, Build Pack).

## Workflow

1.  **Analysis (Анализ текущего состояния)**
    * Проверить наличие `Dockerfile`. Если нет — предложить создание на базе Python 3.12-slim.
    * Определить входную точку (для `agent_p_dasbord` это вероятно Streamlit: `streamlit run main.py`).
    * Проверить `requirements.txt` на наличие конфликтующих версий.

2.  **Container Optimization (Оптимизация контейнера)**
    * Внедрить **Multi-stage build** для уменьшения веса.
    * Добавить пользователя `non-root` для безопасности.
    * Убедиться, что `EXPOSE` соответствует порту приложения (стандартно 8501 для Streamlit).
    * Настроить `HEALTHCHECK` (критично для Coolify, чтобы определить статус сервиса).

3.  **Coolify Configuration (Конфигурация Coolify)**
    * Создать/Обновить `docker-compose.prod.yml`.
    * Убрать `build: .` если используется готовый образ, или настроить контекст сборки.
    * Определить `volumes` для персистентных данных (например, для БД SQLite или загруженных файлов).
    * *Важно:* Убедиться, что Streamlit запускается в режиме `headless=true` и слушает `0.0.0.0`.

4.  **Environment Preparation (Подготовка окружения)**
    * Сканировать код на использование `os.getenv` или `config.py`.
    * Сгенерировать список ключей для вставки в раздел "Secrets" в Coolify.

5.  **Final Verification (Финальная проверка)**
    * Проверить синтаксис YAML.
    * Убедиться в отсутствии хардкода секретов в Dockerfile.

## Guardrails

### Safety
* **Никогда** не помещать реальные API-ключи или пароли в `Dockerfile` или `docker-compose.yml`. Использовать переменные окружения (`${VAR_NAME}`).
* Не использовать тег `latest` для базовых образов в продакшене; фиксировать минорные версии (напр. `python:3.12-slim`).

### Fallback
* Если тип приложения не определен, использовать настройки для общего Python скрипта.
* Если `requirements.txt` отсутствует, предупредить пользователя о невозможности сборки.

### Assumptions
* Целевая ОС сервера — Linux (Debian/Ubuntu).
* Coolify использует Docker Engine под капотом.

## Quality Bar

* [ ] `Dockerfile` использует multi-stage сборку.
* [ ] В `docker-compose.prod.yml` определен `restart: always` или `unless-stopped`.
* [ ] Healthcheck корректно настроен (например, `curl -f http://localhost:8501/_stcore/health`).
* [ ] `.dockerignore` существует и исключает `.git`, `.env`, `__pycache__`.
* [ ] Все пути используют прямые слеши (`/`).

## Examples

**Input:**
User: "Подготовь этот дашборд для Coolify."

**Output:**
"Я проанализировал `agent_p_dasbord`.
1. Обновил `Dockerfile`: добавил `HEALTHCHECK` и очистку кэша apt.
2. Создал `docker-compose.prod.yml`: настроил вольюмы для сохранения данных.
3. Вот список переменных, которые нужно добавить в Coolify Secrets:
   - `OPENAI_API_KEY`
   - `DB_PASSWORD`