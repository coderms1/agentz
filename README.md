# 🧠 Multi-Agent AI Hub by sim

👋 Welcome to the Multi-Agent AI Hub — a modular project housing a growing collection of custom-built AI agents designed for a wide variety of tasks. Each agent is developed using different tools, frameworks, and technologies to explore various approaches to automation, data analysis, and interaction.

## 🔧 Technologies Used

- **Python** & **Java** – Core agent logic, utilities, and backend services
- **MongoDB** – Persistent storage for agent memory, metadata, and analytics
- **Render.com** – Hosting for web services, APIs, and background workers
- **Frameworks & APIs** – Each agent may utilize its own set of third-party tools, including REST APIs, AI/LLM integrations, and blockchain interfaces

## 🧩 Project Structure

The repo is organized into agent-specific directories. Each folder contains code, documentation, and assets relevant to that agent's function.

```bash
/trench0r_bot/
  |- chain_fallback.py
  |- cli_runner.py
  |- config.py
  |- data_bot.py
  |- data_fetcher.py
  |- interaction_log.txt
  |- logger_bot.py
  |- personality_bot.py
  |- predictor_bot.py
  |- price_fetcher.py
  |- profile_bot.py
  |- requirements.txt
  |- score_utils.py
  |- strategist_bot.py
  |- telegram_bot.py
  |- trench0r_handler.py
  |- web_ui.py
  |- x_listener.py
  |- README.md

/smith_1/
  |- .gitignore
  |- sm1th_1.0.py
  |- tools.py

/whizper_agent/
  |- 01_main.py
  |- 02_tg_bot.py
  |- 03_persona.py
  |- 04_btc_report.py

shared files/
  |- utils/
  |- db/
  |- config/
