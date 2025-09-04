```markdown
```
# AI-Powered Procurement Automation Platform

This project provides an **AI-driven procurement automation platform** designed to assist councils and organizations in generating, managing, and evaluating tender documents.  
It integrates **FastAPI services** (for document processing, TEPP generation, supplier response ingestion, etc.) with a **Streamlit user interface** for an interactive, user-friendly workflow.
```
---

## 📂 Project Structure



AI-Powered-Procurement-Automation-Platform/
│
├── app/                     # FastAPI backend (routers, services, TEPP logic)
│   ├── routers/             # API endpoints
│   ├── services/            # Core processing logic
│   ├── vectorstores/        # Vector DB integrations
│   └── ...
│
├── app/streamlit\_app.py     # Streamlit frontend (tender UI)
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
└── ...

````

---

## ⚙️ Requirements

- Python 3.10+
- [Conda](https://docs.conda.io/en/latest/miniconda.html) or `venv`
- Install dependencies:

```bash
pip install -r requirements.txt
````

---

## 🚀 Running the Application

The project consists of **two parts**:

1. **FastAPI backend** (document processing + APIs)
2. **Streamlit frontend** (interactive UI for users)

You need both running in parallel.

### 1. Launch FastAPI (Backend)

```bash
# From the project root
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* API will be available at: [http://localhost:8000](http://localhost:8000)
* Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Launch Streamlit (Frontend)

```bash
# From the project root
streamlit run app/streamlit_app.py --server.port 8501
```

* UI will be available at: [http://localhost:8501](http://localhost:8501)

---

## 📝 Typical Workflow

1. Open the **Streamlit UI**.
2. Select an **AI model**, tender category, and purchase category.
3. Upload the **technical specification** (PDF/DOCX).
4. System generates:

   * **TEPP** (Tender Evaluation and Procurement Plan)
   * **Returnable Schedules**
   * **RFT (Request for Tender)** draft
5. Review and edit results inside the UI.
6. Download as Word documents for Council submission.

---

## 📌 Notes

* Ensure the **backend (Uvicorn)** is running before using Streamlit, otherwise the UI won’t be able to fetch data.
* Vectorstore indexes are cached locally to speed up repeated runs.
* This project is modular and can be extended for different procurement domains (HVAC, trucks, electrical works, etc.).

---

## 👨‍💻 Development

For development, it’s recommended to use a Conda environment:

```bash
conda create -n AI310 python=3.10
conda activate AI310
pip install -r requirements.txt
```

---

## 📄 License

MIT License






