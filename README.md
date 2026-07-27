## \# 🤖 RON



#### An advanced, hybrid AI desktop assistant built for speed, privacy, and seamless voice control.

#### RON is designed to provide powerful desktop automation, context-aware intent parsing, and intelligent assistance entirely on your local machine—with an optional Cloud Performance Mode for lightning-fast responses.

#### \---

## \## 🌟 Key Features



#### \* \*\*Hybrid AI Engine (Local \& Cloud):\*\* Run RON 100% locally using Llama 3 (via Ollama) for total privacy, or switch to Cloud Performance Mode (via Gemini API) for instantaneous 1-second execution.



#### \* \*\*Lightning-Fast Voice Chat:\*\* Features a highly optimized, lag-free voice mode. Built with Dynamic Voice Activity Detection (VAD) that filters out background laptop fan noise, and native Windows SAPI for crash-proof, instant Text-To-Speech.



#### \* \*\*Continuous Follow-Up:\*\* Talk to RON naturally. After his first reply, RON's microphone stays open for seamless follow-up commands—no need to repeat wake words.



#### \* \*\*Advanced Intent Parsing:\*\* High-accuracy natural language processing that understands complex automation chaining (e.g., \*"open notepad, write a poem, and close it after 10 seconds"\*). Includes intelligent pronoun resolution so RON remembers what "it" refers to.



#### \* \*\*Desktop Automation:\*\* Autonomously handles local tasks, system shortcuts, simulated typing, and app management completely silently in the background.



#### \* \*\*Safety First:\*\* Built-in local safety manager and sandbox to protect system integrity during execution.

#### \---

## \## 🏗️ Project Architecture



#### The repository is structured for clean modular execution:

#### ```text

#### ├── ron\_agent/

#### │   ├── automation.py       # Local execution, keystroke simulation, and desktop automation

#### │   ├── intent\_parser.py    # Natural language processing, regex chaining, and LLM routing

#### │   ├── ron\_engine.py       # Core orchestrator managing UI, memory, and task dispatching

#### │   ├── ron\_ui.py           # Custom desktop user interface layer

#### │   ├── safety\_manager.py   # Local runtime safety checks and guardrails

#### │   └── voice\_manager.py    # VAD, STT, and native Windows SAPI Text-to-Speech handling

#### ├── ron\_config.json         # Global application configurations

#### ├── run\_ron.bat             # Quick-launch Windows batch script

#### └── validate\_ron.py         # System verification and dependency checker

#### \---

## 🚀 Getting Started



### Prerequisites



#### OS: Windows 10/11

#### Python: Version 3.10 or higher

#### Local LLM Engine: Ollama installed locally with the llama3 model pulled (https://ollama.com).

#### Installation \& Launch

#### Clone this repository to your local machine.

#### (Optional but Recommended) For lightning-fast Cloud Performance Mode, create a file named gemini\_api\_key.txt in the main folder and paste your free Google Gemini API key inside it.

#### Ensure Ollama is running in the background by executing: ollama run llama3

#### Double-click run\_ron.bat or execute the main UI wrapper to launch the desktop assistant!



## 🛠️ Tech Stack



#### Language: Python

#### LLM: Meta Llama 3 (via Ollama) \& Google Gemini API (Hybrid)

#### Voice Engine: Google STT \& Windows Native SAPI (win32com)

#### GUI Framework: Custom Tkinter UI components



## 📜 License

#### This project is licensed under the GPL-3.0 License - see the LICENSE file for details.







###### ***\*\*\*RON IS STILL UNDER-DEVELOPMENT HE MAY HAVE BUGS, IF YOU FIND ANY BUGS PLEASE REPORT THEM\*\*\****



