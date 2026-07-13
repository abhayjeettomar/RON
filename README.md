# \# 🤖 RON

##### 

##### An offline, privacy-first AI desktop assistant powered by Llama 3 and Ollama.

##### 

##### RON is built to provide powerful desktop automation, intent parsing, and intelligent assistance entirely on your local machine—meaning your data, system info, and conversations never leave your computer.

##### 

##### \---

##### 

### \## 🌟 Key Features

##### 

##### \* \*\*100% Offline \& Private:\*\* Powered locally by Ollama and Llama 3. No cloud API keys, no data tracking, and total privacy.

##### \* \*\*Intent Parsing:\*\* High-accuracy natural language processing to understand exactly what desktop actions you want to perform.

##### \* \*\*Desktop Automation:\*\* Handles local tasks, system shortcuts, and routine workflows autonomously.

##### \* \*\*Safety First:\*\* Built-in local safety manager to protect system integrity during execution.

##### \* \*\*Custom UI \& Avatar:\*\* Features a dedicated desktop interface with visual avatar branding assets.

##### 

##### \---

##### 

### \## 🏗️ Project Architecture

##### 

##### The repository is structured for clean modular execution:

##### 

##### ├── ron\_agent/

##### │   ├── automation.py       # Local execution and desktop automation scripts

##### │   ├── intent\_parser.py    # Natural language processing and intent analysis

##### │   ├── ron\_engine.py       # Core LLM orchestrator connecting to Ollama

##### │   ├── ron\_ui.py           # Desktop user interface layer

##### │   └── safety\_manager.py   # Local runtime safety checks and guardrails

##### ├── ron\_config.json         # Layout and application configurations

##### ├── run\_ron.bat             # Quick-launch Windows batch script

##### └── validate\_ron.py         # System verification and dependency checker

##### 

##### \---

##### 

### \## 🚀 Getting Started

##### 

#### \### Prerequisites

##### \* \*\*OS:\*\* Windows 10/11

##### \* \*\*Python:\*\* Version 3.10 or higher

##### \* \*\*LLM Engine:\*\* Ollama installed locally with the llama3 model pulled.(https://ollama.com)

##### 

#### \### Installation \& Launch

##### 1\. Clone this repository to your local machine.

##### 2\. Ensure Ollama is running in the background by executing: ollama run llama3

##### 4\. Double-click run\_ron.bat or execute the main UI wrapper to launch the desktop assistant!

##### 

##### \---

##### 

### \## 🛠️ Tech Stack

##### \* \*\*Language:\*\* Python

##### \* \*\*LLM:\*\* Meta Llama 3 (via Ollama)

##### \* \*\*GUI Framework:\*\* Tkinter / Custom Python UI components

##### 

##### \---

##### 

### \## 📜 License

##### This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

