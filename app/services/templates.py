# app/services/templates.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..config import settings

# Directory where JSON templates live
TEMPLATE_DIR = settings.DATA_DIR / "templates"
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# Template filenames (stored separately on disk)
RETURNABLES_TEMPLATE_FILE = TEMPLATE_DIR / "returnables_template.json"
RFT_TEMPLATE_FILE         = TEMPLATE_DIR / "rft_template.json"
TEPP_TEMPLATE_FILE        = TEMPLATE_DIR / "tepp_template.json"


# ---------- small file utils ----------
def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Template not found: {path}. "
            f"Please add your JSON template under: {TEMPLATE_DIR}/"
        ) from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in template: {path}. Please fix the file contents."
        ) from e

def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- template loaders ----------
def load_returnables_template() -> Dict[str, Any]:
    """Load the Returnables skeleton from DATA_DIR/templates/returnables_template.json."""
    return read_json(RETURNABLES_TEMPLATE_FILE)

def load_rft_template() -> Dict[str, Any]:
    """Load the RFT skeleton from DATA_DIR/templates/rft_template.json."""
    return read_json(RFT_TEMPLATE_FILE)

# app/services/templates.py
from typing import Dict, Any

def load_tepp_template() -> Dict[str, Any]:
    """
    Council-style TEPP template matching the provided document structure.
    This is the SOURCE OF TRUTH shape your compose_tepp should fill.
    """
    return {
        "document_metadata": {
            "document_title": "",          # e.g., Tender Evaluation and Probity Plan
            "tender_number": "",           # e.g., C11/2025
            "project_name": "",            # e.g., MAIN POOL HALL ...
            "term": "",                    # e.g., For a term of 12 months.
            "date": "",
            "version": "",
            "prepared_by": "",
            "approved_by": ""
        },

        # Optional explicit TOC (you can re-generate when rendering)
        "table_of_contents": [
            {"n": "1.", "title": "Aim"},
            {"n": "2.", "title": "Description of Requirement"},
            {"n": "2.1", "title": "Desired Outcomes"},
            {"n": "2.2", "title": "Purpose of Request for Tender (RFT)"},
            {"n": "3.", "title": "Probity and Accountability"},
            {"n": "3.1", "title": "Probity"},
            {"n": "3.2", "title": "Confidentiality and Conflict of Interest"},
            {"n": "3.3", "title": "Security and Confidentiality"},
            {"n": "3.4", "title": "Authorised Contact Officer"},
            {"n": "3.5", "title": "Advertising the RFT"},
            {"n": "3.6", "title": "Receipt of Tenders"},
            {"n": "3.7", "title": "Late Tenders"},
            {"n": "3.8", "title": "Requests for Clarification"},
            {"n": "3.9", "title": "Critical issues or risks"},
            {"n": "4.", "title": "Evaluation Committee"},
            {"n": "5.", "title": "Evaluation Schedule"},
            {"n": "6.", "title": "Tender Evaluation"},
            {"n": "6.1", "title": "Evaluation Methodology"},
            {"n": "6.1.1", "title": "Compliance Criteria"},
            {"n": "6.1.2", "title": "Required Criteria"},
            {"n": "6.2", "title": "Returnable Schedules Scoring"},
            {"n": "7.", "title": "Pricing"},
            {"n": "7.1.1", "title": "Pricing Model"},
            {"n": "7.1.2", "title": "Local Preference Policy"},
            {"n": "7.1.3", "title": "Value for Money"},
            {"n": "7.1.4", "title": "Interviews and Presentation Criteria"},
            {"n": "7.2", "title": "Short-listing / Setting Aside Tenders"},
            {"n": "7.3", "title": "Alternative Tenders"},
            {"n": "7.4", "title": "Tenderer Presentations"},
            {"n": "7.5", "title": "Evaluation Report"},
            {"n": "8.", "title": "Contract Negotiations"},
            {"n": "9.", "title": "Debriefing of Unsuccessful Tenderers"},
            {"n": "10.", "title": "Contract Management"},
            {"n": "11.", "title": "Critical dates"},
            {"n": "12.", "title": "How to Complete the TEPP"}
        ],

        # 1. Aim
        "aim": {
            "intro": "",  # dynamic: your project one-liner
            "body": (
                "This Tender Evaluation and Probity Plan (TEPP) is the planning and control document "
                "for conducting the evaluation of Tenders received in response to the RFT.\n"
                "The TEPP sets out:\n"
                "• the processes and principles to be followed when evaluating Tenders;\n"
                "• individuals’ responsibilities;\n"
                "• the evaluation schedule; and\n"
                "• reporting requirements."
            )
        },

        # 2. Description of Requirement
        "description_of_requirement": {
            "summary": [],          # dynamic bullet points (General/Technical/Electrical/etc.)
            "general": [],          # “General:” bullets
            "technical_requirements": {
                "decommissioning_removal": [],
                "supply_installation": [],
                "electrical_controls": [],
                "hoisting_cranage": [],
                "testing_commissioning": [],
                "maintenance_warranty": [],
            },
            "invoicing": [],
            "reporting": {
                "weekly": [],
                "final": []
            },
            "performance_monitoring": {
                "note": "",
                "criteria": []
            }
        },

        # 2.1 Desired Outcomes
        "desired_outcomes": [],

        # 2.2 Purpose of RFT
        "purpose_rft": [],

        # 3. Probity and Accountability
        "probity_and_accountability": {
            "probity": "",  # stable policy text (default filled below)
            "confidentiality_and_conflict": "",
            "security_and_confidentiality": "",
            "authorised_contact_officer": {
                "name": None,
                "title": None,
                "email": None,
                "phone": None
            },
            "advertising_rft": "",
            "receipt_of_tenders": "",
            "late_tenders": "",
            "requests_for_clarification": "",
            "critical_issues_or_risks": [   # table rows: Issue/Risk, Consequences, Action
                # {"issue": "", "consequence": "", "action": ""}
            ]
        },

        # 4. Evaluation Committee (table)
        "evaluation_committee": [
            # {"name": "", "title": "", "branch": "", "role": ""}
        ],

        # 5. Evaluation Schedule (table)
        "evaluation_schedule": [
            # {"task": "", "responsibility": "", "due": ""}
        ],

        # 6. Tender Evaluation
        "tender_evaluation": {
            "methodology_text": "The Evaluation Committee, in accordance with the methodology specified in the RFT and reproduced here, will evaluate all tenders.",
            "evaluation_methodology": {
                "compliance_criteria": [
                    {"criterion": "Tender Details", "weight": "Nil"},
                    {"criterion": "Compliance of RFT Terms & Conditions", "weight": "Nil"},
                    {"criterion": "Tenderer’s Statutory Declaration", "weight": "Nil"}
                ],
                "required_criteria_table": [  # dynamic — from your weighting logic
                    # {"criterion": "...", "weight": "12.5%"}
                ]
            },

            # 6.2 Returnable schedules scoring
            "returnable_schedules_scoring": {
                # (full scales omitted here for brevity – see file)
            }
        },

        # 7. Pricing & subclauses
        "pricing": {
            "pricing_model_text": (
                "Pricing for tender evaluation will be normalised; the lowest fee achieves the maximum score "
                "(equal to the price weighting). State Government method:\n"
                "Ps = 200 – (Pc / Pav × 100)\nPn = Ps / 200\nPw = Pn × [Price Weight]\n"
                "Pc = Total Net Cost, Pav = Average of Total Net Costs."
            ),
            "local_preference_policy": {
                "policy_text": (
                    "Local Preference Policy per Procurement Policy P000553.1: "
                    "5% discount (cap $50,000) for suppliers in Blacktown LGA; "
                    "2.5% discount (cap $25,000) for suppliers located in Western Sydney Councils."
                ),
                "western_sydney_councils": [
                    "Blue Mountains City Council","City of Parramatta Council","Cumberland City Council",
                    "Fairfield City Council","Hawkesbury City Council","Liverpool City Council",
                    "Parramatta City Council","Penrith City Council","The Hills Shire Council"
                ],
                "application_note": "Record eligible addresses in the evaluation spreadsheet (third tab)."
            },
            "value_for_money": (
                "Assessed on qualitative outcomes + price: quality and fitness for purpose vs whole-of-life costs vs risk."
            ),
            "interviews_and_presentation_criteria": "Scores may be revised following interviews/presentations of shortlisted tenderers."
        },

        "shortlisting": "Clearly non-competitive tenders may be excluded with reasons recorded.",
        "alternative_tenders": "Alternative tenders will be evaluated per the RFT methodology.",
        "tenderer_presentations": "Interviews may be used for clarification only; no new information is accepted.",
        "evaluation_report": (
            "Final results documented in a Council Report: method, number of tenders, rankings, recommendation, and rationale. "
            "Considered by the Tender Review Committee; endorsed and presented to Council."
        ),

        "contract_negotiations": (
            "Negotiations (post-tender) are fair, open, and must not materially change requirements. Outcomes documented."
        ),
        "debriefing_unsuccessful": (
            "Debriefing may be offered upon request. Only general comments on the tenderer’s own submission; "
            "no comparisons; no scoring details."
        ),
        "contract_management": "The contract will be managed by <role/name>.",
        "critical_dates": [],  # e.g., ["Commencement required by Aug 2025"]
        "how_to_complete_tepp": [
            "1) Title Page — Replace Tender Number, Name and Term.",
            "2) 1. Aim — Update Tender Name and Term.",
            "3) 2. Description of Requirement — Replace with contract description and main requirements.",
            "4) 2.1 Desired Outcomes — Insert procurement outcomes (value for money, timely delivery, etc.).",
            "5) 2.2 Purpose of RFT — Replace with reasons for this tender (or EOI/Quotation).",
            "… (continue your internal guidance list as needed) …",
            "Update footer to correct Tender Number and Tender Name."
        ]
    }