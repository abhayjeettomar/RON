### \# 🤖 RON - Advanced Hybrid AI Desktop Assistant

###### 

###### An advanced, hybrid AI desktop assistant built for speed, privacy, and seamless voice control.

###### 

###### I designed RON to provide powerful desktop automation, context-aware intent parsing, and intelligent assistance entirely on your local machine—with an optional Cloud Performance Mode for lightning-fast responses.

###### 

###### > ⚠️ \*\*Beta Notice:\*\* RON is actively under development! You may encounter minor bugs or edge cases. If you find any issues or have feature suggestions, please open an issue in the \*\*\[Issues](../../issues)\*\* tab.

###### 

###### \---

###### 

### \## 🚀 Download Beta

###### 

###### Prefer not to run from source? Grab my pre-compiled standalone executable from the latest release:

###### 

###### 👉 \*\*\[Download RON Beta (.exe)](../../releases)\*\*

###### 

###### \---

###### 

### \## 🌟 Key Features

###### 

###### \* \*\*Hybrid AI Engine (Local \& Cloud):\*\* Run RON 100% locally using Llama 3 (via Ollama) for total privacy, or switch to Cloud Performance Mode (via Gemini API) for instantaneous 1-second execution.

###### \* \*\*Lightning-Fast Voice Chat:\*\* Features a highly optimized, lag-free voice mode. Built with Dynamic Voice Activity Detection (VAD) that filters out background laptop fan noise, and native Windows SAPI for crash-proof, instant Text-To-Speech.

###### \* \*\*Continuous Follow-Up:\*\* Talk to RON naturally. After his first reply, RON's microphone stays open for seamless follow-up commands—no need to repeat wake words.

###### \* \*\*Advanced Intent Parsing:\*\* High-accuracy natural language processing that understands complex automation chaining (e.g., \*"open notepad, write a poem, and close it after 10 seconds"\*). Includes intelligent pronoun resolution so RON remembers what "it" refers to.

###### \* \*\*Desktop Automation:\*\* Autonomously handles local tasks, system shortcuts, simulated typing, and app management completely silently in the background.

###### \* \*\*Safety First:\*\* Built-in local safety manager and sandbox to protect system integrity during execution.

###### 

###### \---

###### 

### \## 🏗️ Project Architecture

###### 

###### The repository is structured for clean modular execution:

###### 

###### ├── ron\_agent/

###### │   ├── automation.py      # Local execution, keystroke simulation, and desktop automation

###### │   ├── intent\_parser.py   # Natural language processing, regex chaining, and LLM routing

###### │   ├── ron\_engine.py      # Core orchestrator managing UI, memory, and task dispatching

###### │   ├── ron\_ui.py          # Custom desktop user interface layer

###### │   ├── safety\_manager.py  # Local runtime safety checks and guardrails

###### │   └── voice\_manager.py   # VAD, STT, and native Windows SAPI Text-to-Speech handling

###### ├── ron\_config.json        # Global application configurations

###### ├── run\_ron.bat            # Quick-launch Windows batch script

###### └── validate\_ron.py        # System verification and dependency checker

###### 

###### \---

###### 

### \## ⚙️ Getting Started

###### 

#### \### Prerequisites

###### 

###### \* \*\*OS:\*\* Windows 10 / 11

###### \* \*\*Python:\*\* Version 3.10 or higher

###### \* \*\*Local LLM Engine:\*\* \[Ollama](https://ollama.com) installed locally with the Llama 3 model pulled (`ollama pull llama3`).

###### 

#### \### Installation \& Launch (From Source)

###### 

###### 1\. \*\*Clone the repository:\*\*

###### &#x20;  git clone https://github.com/your-username/your-repo-name.git

###### &#x20;  cd your-repo-name

###### 

###### 2\. \*\*(Optional) Set up Cloud Mode:\*\*

###### &#x20;  For lightning-fast Cloud Performance Mode, create a file named `gemini\_api\_key.txt` in the root folder and paste your free Google Gemini API key inside it.

###### 

###### 3\. \*\*Ensure Ollama is running:\*\*

###### &#x20;  ollama run llama3

###### 

###### 4\. \*\*Launch RON:\*\*

###### &#x20;  Double-click `run\_ron.bat` or run the main script directly to launch the desktop assistant!

###### 

###### \---

###### 

### \## 🛠️ Tech Stack

###### 

###### \* \*\*Language:\*\* Python

###### \* \*\*LLM Engine:\*\* Meta Llama 3 (via Ollama) \& Google Gemini API (Hybrid)

###### \* \*\*Voice Engine:\*\* Google STT \& Windows Native SAPI (`win32com`)

###### \* \*\*GUI Framework:\*\* Custom Tkinter UI components

###### 

###### \---

###### 

### \## 📜 License

###### 

###### This project is licensed under the GPL-3.0 License - see the \[LICENSE](LICENSE) file for details.

