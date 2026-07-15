# SkyCast

Enterprise climate intelligence platform integrating 5 data sources with periodic monitoring and alerting.

[Full Case Study](https://juandelaf1.github.io/projects/sky-cast)

## Overview

SkyCast ingests data from 5 sources (AEMET, OpenWeatherMap, AirNOW, Open-Meteo, custom IoT sensors) into a unified PostgreSQL schema. A FastAPI backend processes and validates data, with Streamlit dashboards for interactive visualization.

## Key Results

- **158 automated tests** across ingestion, validation, and API layers
- **Periodic monitoring** (not real-time) via scheduled ETL
- **5 data sources** integrated under a unified schema
- **CI/CD pipeline** with automated testing

## Stack

FastAPI - PostgreSQL - Streamlit - Docker - Python - AEMET API

## Architecture

Data Sources - Ingestion - PostgreSQL - FastAPI - Streamlit Dashboard

## Limitations

- Periodic monitoring rather than real-time streaming
- IoT sensor integration experimental (simulated test data)
- Single-server deployment

---

*Detailed architecture decisions and trade-offs at juandelaf1.github.io/projects/sky-cast*