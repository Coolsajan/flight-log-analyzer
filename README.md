# ✈️ Flight Log Analysis Project

This project is designed to analyze flight log data, identify potential risk situations, and generate actionable reports using multi-agent systems and AI-driven insights.

## 📌 Features

- 📊 Data ingestion and preprocessing from flight logs
- 🧠 Multi-agent analysis pipeline:
  - Agent 1: Reads the Log Image and Analyze
  - Agent 2: Reads the analysis and assort the risk situation
  - Agent 3: Reads the risk situation and generates the report
  - Agent 4: Reads the generated report and communication with necessary team
  - Agent 5: Reads the report and provides the quality assurance.
- 🛬 Detection of anomalies or risky behavior
- 📑 Report generation with risk assessment
- 🚀 Easily extendable and scalable

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Pandas / NumPy** - Data manipulation
- **AutoGen** - Multi-agent architecture
- **Gemini** - LLM-powered analysis
- **Streamlit** - For UI

---

## 📁 Project Structure

```bash
flight-analysis/
│
├── main.py                   # Main ui with streamlit code
├── backend/
│  ├── backend_agent.py    # Multi-agent system script
├── utils.py            # Helper functions
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Setup Instructions

#### 1._Clone The Repo_

```
git clone https://github.com/Coolsajan/flight-log-analyzer.git
cd flight-analysis
```

#### 2._Create A virtual env_

```
python -m venv venv(name)
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3._Instal all dependencies_

```
pip install -r requirements.txt
```

#### 4. _Update the .env file_

`Create a .env file as add the gmails password,llm api key , sender and receiver email.`

#### 5. _Run the project_

```
streamlit run main.py
```
