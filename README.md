---
title: FlexGuard
emoji: 🏃
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.28.0
python_version: '3.12'
app_file: app.py
pinned: false
---

FlexGuard

FlexGuard is a reliability testing project for offline field applications.

The project checks what happens when an application faces problems like:

* internet connection loss
* slow network
* server errors
* interrupted uploads
* duplicate requests
* failed synchronisation

FlexGuard will create these failure situations and check whether important inspection data stays safe and correct.
The project also includes a small demo application called FieldSync.
FieldSync is used only for testing FlexGuard.

Main Goal:

Check that field data is not:
* lost
* duplicated
* corrupted
* incorrectly synchronised

Project Parts:
* FieldSync demo application
* FastAPI backend
* SQLite database
* offline queue
* retry handling
* duplicate protection
* attachment checks
* failure simulation
* automated tests
* reliability scoring
* release checks

Technology:
* Python
* FastAPI
* SQLite
* Pytest
* HTTPX
* GitHub Actions

Current Status:
Project setup complete.

Note:
This is an independent learning and portfolio project.
It is not an official FlexManager product and is not affiliated with FlexManager.