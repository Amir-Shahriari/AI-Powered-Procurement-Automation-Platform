"""
This module provides a high‑level generator for the tenderer‑facing
"Returnable Schedules" document.  The returnable schedules form
part of a tender package and include instructions, a reference
checklist and a series of numbered schedules that the tenderer must
complete and return.  Each schedule captures specific information
about the tenderer (corporate details, financial capacity, key
personnel, insurances, previous experience, service methodology,
pricing, CSR/EEO/WHS policies, modern slavery declarations, etc.).

Unlike the TEPP, which is an internal evaluation document, this
generator outputs a structured JSON representation of the returnable
schedules.  The JSON can be rendered into a DOCX/PDF via a
separate template or used to populate an online form.  Where
possible, the fields are pre‑populated from the provided
`spec_summary` or `parsed` context (e.g. tender title, contract
number, non‑negotiable dates).  The caller may further tailor the
output by editing the returned JSON before conversion to a document.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from app.services.base import unique_keep_order


def _ensure_dict(obj: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Ensure obj[key] is a dict; if not present or wrong type, replace with {} and return it."""
    val = obj.get(key)
    if not isinstance(val, dict):
        obj[key] = {}
    return obj[key]


def _ensure_list_path(root: Dict[str, Any], path: List[str]) -> List[Any]:
    """
    Ensure a nested path exists and is a list at the leaf.
    Any non‑list at the leaf is converted to a single‑item list (unless None -> []).
    Returns the ensured list reference.
    """
    cur = root
    for i, k in enumerate(path):
        last = i == len(path) - 1
        if last:
            v = cur.get(k)
            if v is None:
                cur[k] = []
            elif isinstance(v, list):
                pass
            elif isinstance(v, (str, int, float, bool, dict)):
                cur[k] = [v]
            else:
                cur[k] = []
            return cur[k]
        else:
            v = cur.get(k)
            if not isinstance(v, dict):
                cur[k] = {}
            cur = cur[k]
    return []


def compose_returnable_schedules(spec_summary: Any,
                                           parsed: Dict[str, Any],
                                           non_negotiable_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Assemble the returnable schedules pack as a structured JSON object.

    Parameters
    ----------
    spec_summary: Any
        A summary object with attributes such as `title`, `contract_no` or
        `tender_no`, and other identifiers.  Strings are extracted via
        getattr with sensible defaults.
    parsed: Dict[str, Any]
        Parsed metadata from the specification.  Fields used include
        `trim_file_no`, `contract_number`, `project_name`, and any
        domain‑specific milestones/dates for Schedule 9 and Schedule 10.
    non_negotiable_date: Optional[str]
        A fixed operational commencement date (e.g., "25 Aug 2025").
        If provided, it is inserted into Schedule 9 to alert tenderers
        of mandatory timing requirements.

    Returns
    -------
    Dict[str, Any]
        A nested dict representing the returnable schedules document.  It
        includes metadata, instructions, supporting information, a
        reference checklist, each of the sixteen schedules, and the WHS
        appendices.  The caller can serialise this dict to JSON or feed
        it into a templating engine to produce a DOCX/PDF.
    """
    # Extract global identifiers with fallbacks
    project_title = getattr(spec_summary, 'title', '') or parsed.get('project_name') or ''
    contract_number = getattr(spec_summary, 'contract_no', '') or getattr(spec_summary, 'tender_no', '') or parsed.get('contract_number') or ''
    trim_file_no = parsed.get('trim_file_no') or getattr(spec_summary, 'trim_file_no', '') or ''
    part_label = parsed.get('part_label') or 'Part 5 Returnable Schedules'
    procurement_type = parsed.get('procurement_type') or 'Request for tender'
    site_name = parsed.get('site_name') or ''
    tenderer_placeholder = '(Tenderer Name)'

    # Build metadata section
    doc: Dict[str, Any] = {}
    doc['metadata'] = {
        'part_label': part_label,
        'procurement_type': procurement_type,
        'project_title': project_title,
        'site': site_name,
        'contract_number': contract_number,
        'trim_file_number': trim_file_no,
        'tenderer_placeholder': tenderer_placeholder,
    }

    # Instructions & submission rules
    doc['instructions'] = [
        "Use the provided templates to complete the required Schedules.",
        "Provide the requested information using the DOCX file and submit as a PDF.",
        "If a schedule does not have enough space, include the information in a separate attachment and reference it in the schedule.",
        "Unless otherwise stated, all documents (schedules and supporting documents) must be submitted in PDF format.",
        "Prices in Schedule 10 must be clear and unambiguous; replace zero/blank with 'included' or 'excluded' and provide an explanation if necessary. Council may reject tenders with ambiguous pricing.",
    ]

    # Supporting information required from tenderers
    doc['supporting_information'] = [
        "Compliance with the tender requirements",
        "Relevant experience, qualifications and licences",
        "Capacity, including past performance and resources",
        "Methodology to undertake the works",
        "Management & financial capacity (including financial statements for the last 3 years)",
        "Quality management (policy, management plan, forms and checklists)",
        "WHS management (completed Council WHS forms, WHS policy & plan, safe work method statements, checklists and forms)",
        "Sustainable environmental management (policy and plan)",
        "Copies of certificates for required third‑party accreditations and insurances",
        "Equal employment opportunity and fair employment evidence",
        "Any additional relevant information that may assist in assessing the tender",
    ]

    # Reference checklist for the tenderer
    schedules_list = [
        {'schedule': 'Schedule 1', 'title': 'Corporate information & Declaration'},
        {'schedule': 'Schedule 2', 'title': 'Financial capacity'},
        {'schedule': 'Schedule 3', 'title': 'Confidentiality and Conflict of Interest'},
        {'schedule': 'Schedule 4', 'title': 'Key personnel'},
        {'schedule': 'Schedule 5', 'title': 'Insurance'},
        {'schedule': 'Schedule 6', 'title': 'Previous experience'},
        {'schedule': 'Schedule 7', 'title': 'Current council clients'},
        {'schedule': 'Schedule 8', 'title': 'Referees'},
        {'schedule': 'Schedule 9', 'title': 'Service delivery & performance'},
        {'schedule': 'Schedule 10', 'title': 'Fee structure'},
        {'schedule': 'Schedule 11', 'title': 'Corporate social responsibility'},
        {'schedule': 'Schedule 12', 'title': 'Sustainability'},
        {'schedule': 'Schedule 13', 'title': 'Equal employment opportunity & fair employment'},
        {'schedule': 'Schedule 14', 'title': 'Work, health & safety'},
        {'schedule': 'Schedule 15', 'title': 'Modern slavery questionnaire'},
        {'schedule': 'Schedule 16', 'title': 'Acknowledgement of addenda & Tenderer’s declaration'},
    ]
    supporting_docs_list = [
        "Certificates of incorporation/registration", 
        "Insurance certificates of currency", 
        "Third‑party accreditation certificates", 
        "Curriculum vitae/licences for key personnel", 
        "Quality management plans and inspection test plans", 
        "WHS manuals, policies, sample checklists and forms", 
        "Environmental management plans", 
        "EEO policy documents", 
        "Financial statements", 
        "Product catalogues/technical sheets", 
        "Draft layout diagrams", 
        "Warranty terms and conditions",
    ]
    doc['reference_checklist'] = {
        'schedules': schedules_list,
        'supporting_documents': supporting_docs_list,
    }

    # Define each schedule as a dict with title and fields/instructions
    schedules: List[Dict[str, Any]] = []

    # Schedule 1 – Corporate Information & Declaration
    schedules.append({
        'schedule': 'Schedule 1',
        'title': 'Corporate Information & Declaration',
        'sections': [
            {
                'heading': 'Company Details',
                'fields': [
                    'Legal Name (as per ASIC)',
                    'Trading Name',
                    'ABN/ACN',
                    'Entity Type (e.g., Pty Ltd, Partnership, Sole Trader)',
                    'Registered Address',
                    'Trading Address',
                    'Contact Person',
                    'Phone',
                    'Email',
                ],
            },
            {
                'heading': 'Declaration',
                'content': (
                    "I/We declare that we have read and understood the Conditions of Tendering and agree to be bound by them, "
                    "that we are solvent and not under any form of external administration, that we have disclosed any conflicts of interest, "
                    "that we hold or will obtain the required insurances and licences, and that this tender constitutes a firm offer for the period specified."
                ),
            },
        ],
    })

    # Schedule 2 – Financial Capacity
    schedules.append({
        'schedule': 'Schedule 2',
        'title': 'Financial Capacity',
        'sections': [
            {
                'heading': 'Banking Details',
                'fields': [
                    'Bank Name',
                    'Branch',
                    'Account Name',
                    'BSB & Account Number',
                ],
            },
            {
                'heading': 'Accountant Details',
                'fields': [
                    'Accountant/Firm Name',
                    'Address',
                    'Contact Name',
                    'Phone',
                    'Email',
                ],
            },
            {
                'heading': 'Financial Statements',
                'content': (
                    "Provide annual financial statements (balance sheet and profit/loss) for the last three years. "
                    "If statements cannot be provided, explain why and supply alternative evidence of financial capacity."
                ),
            },
        ],
    })

    # Schedule 3 – Confidentiality & Conflict of Interest
    schedules.append({
        'schedule': 'Schedule 3',
        'title': 'Confidentiality & Conflict of Interest',
        'sections': [
            {
                'heading': 'Confidentiality',
                'content': (
                    "Acknowledge that all information provided by Council is confidential and must not be disclosed except as permitted."
                ),
            },
            {
                'heading': 'Conflict of Interest',
                'content': (
                    "Disclose any actual, potential or perceived conflicts of interest that may influence your ability to perform the contract. "
                    "Include details of the conflict and the proposed mitigation strategy."
                ),
                'table': {
                    'columns': ['Conflict Description', 'Impact', 'Mitigation Strategy'],
                    'rows': [],
                },
            },
            {
                'heading': 'ICAC Guidance',
                'content': (
                    "Refer to NSW ICAC guidance on managing conflicts of interest in procurement for further information."
                ),
            },
        ],
    })

    # Schedule 4 – Key Personnel
    schedules.append({
        'schedule': 'Schedule 4',
        'title': 'Key Personnel',
        'sections': [
            {
                'heading': 'Personnel Details',
                'table': {
                    'columns': ['Name', 'Proposed Role', 'Qualifications / Experience', 'Years in Role'],
                    'rows': [],
                },
            },
            {
                'heading': 'Supporting Documents',
                'content': (
                    "Attach curriculum vitae and/or licences evidencing qualifications and experience for each proposed key personnel."
                ),
            },
        ],
    })

    # Schedule 5 – Insurance
    schedules.append({
        'schedule': 'Schedule 5',
        'title': 'Insurance',
        'sections': [
            {
                'heading': 'Insurance Certificates',
                'table': {
                    'columns': ['Insurance Type', 'Insurer', 'Policy Number', 'Limit of Indemnity', 'Expiry Date', 'Certificate Attached (Y/N)'],
                    'rows': [
                        ['Public Liability (min $20m)', '', '', '', '', ''],
                        ['Professional Indemnity (min $10m – maintained 7 years post‑expiry)', '', '', '', '', ''],
                        ['Product Liability (min $10m)', '', '', '', '', ''],
                        ['Workers’ Compensation (as required under NSW law)', '', '', '', '', ''],
                    ],
                },
            },
            {
                'heading': 'Subcontractor Insurances',
                'table': {
                    'columns': ['Subcontractor Name', 'Insurance Type', 'Limit of Indemnity', 'Expiry Date'],
                    'rows': [],
                },
                'content': "List insurances held by all subcontractors. Tenderers may be required to increase cover limits if Council deems necessary.",
            },
        ],
    })

    # Schedule 6 – Previous Experience
    schedules.append({
        'schedule': 'Schedule 6',
        'title': 'Previous Experience',
        'sections': [
            {
                'heading': 'Relevant Projects',
                'content': "Provide details of at least three relevant projects completed in the last five years, including client name, project description, contract value, start and finish dates, and your scope of work.",
                'table': {
                    'columns': ['Client', 'Project Description', 'Contract Value', 'Start Date', 'Completion Date', 'Scope of Work'],
                    'rows': [],
                },
            },
        ],
    })

    # Schedule 7 – Current Council Clients
    schedules.append({
        'schedule': 'Schedule 7',
        'title': 'Current Council Clients',
        'sections': [
            {
                'heading': 'Councils Serviced',
                'content': "List any councils or local government organisations you are currently providing services to and the number of years you have been engaged.",
                'table': {
                    'columns': ['Council', 'Years of Service'],
                    'rows': [],
                },
            },
        ],
    })

    # Schedule 8 – Referees
    schedules.append({
        'schedule': 'Schedule 8',
        'title': 'Referees',
        'sections': [
            {
                'heading': 'Client Referees',
                'content': "Provide details for at least two senior client referees (up to four may be provided).",
                'table': {
                    'columns': ['Organisation', 'Project', 'Years (From–To)', 'Contact Name', 'Position', 'Phone', 'Email'],
                    'rows': [],
                },
            },
        ],
    })

    # Schedule 9 – Service Delivery & Performance
    # This schedule is highly project‑specific.  Use parsed context for milestones and mandatory dates where available.
    milestones_table = {
        'columns': ['Milestone Description', 'Target Date'],
        'rows': []
    }
    # Pre‑populate a generic set of milestones; caller may override or extend
    default_milestones = [
        'Site establishment',
        'Removal of existing equipment',
        'Delivery and installation of major equipment',
        'Mechanical and electrical integration',
        'Testing & commissioning',
        'Handover and defects liability period commencement',
    ]
    for m in default_milestones:
        milestones_table['rows'].append([m, non_negotiable_date or ''])

    schedules.append({
        'schedule': 'Schedule 9',
        'title': 'Service Delivery & Performance',
        'sections': [
            {
                'heading': 'Methodology & Resources',
                'content': (
                    "Describe your methodology for delivering the works, including sequencing of activities, resource allocations "
                    "(personnel, plant, equipment, suppliers and subcontractors), and how you will ensure quality outcomes."
                ),
            },
            {
                'heading': 'Quality & Accreditations',
                'content': (
                    "Outline your quality management system, including reference to any third‑party accreditations and inspection test plans (ITPs). "
                    "Attach sample reports where available."
                ),
            },
            {
                'heading': 'Milestones',
                'table': milestones_table,
                'content': (
                    "Populate the milestones table with the key deliverables for this project. If Council has mandated a fixed date for "
                    "commencement or completion (e.g., start of operations by {date}), ensure your program aligns with that date."
                    .format(date=non_negotiable_date or 'TBA')
                ),
            },
            {
                'heading': 'Disruption Minimisation',
                'content': (
                    "Explain how you will minimise disruption to Council operations and stakeholders during the works."
                ),
            },
            {
                'heading': 'Q&A Confirmations',
                'content': (
                    "Confirm that you will provide the following information as part of your tender or prior to award: "
                    "product catalogues/technical sheets, draft layout diagrams/drawings, crew qualifications and experience, warranty terms, "
                    "equipment origin (country of manufacture), and details of any proposed subcontractors."
                ),
            },
        ],
    })

    # Schedule 10 – Fee Structure
    schedules.append({
        'schedule': 'Schedule 10',
        'title': 'Fee Structure',
        'sections': [
            {
                'heading': 'Performance / Technical Specification',
                'content': (
                    "List the key performance requirements and technical specifications for the major equipment or services to be supplied. "
                    "For example, device capacities, ratings, compliance standards, control interfaces, and any basis‑of‑design references."
                ),
                'table': {
                    'columns': ['Item Description', 'Specification', 'Basis of Design / Reference', 'Quantity'],
                    'rows': [],
                },
            },
            {
                'heading': 'Pricing Table',
                'content': (
                    "Provide a lump sum price in Australian dollars for each scope package. Pricing must include GST, levies, duties, overheads "
                    "and all other costs necessary to perform the works. Prices must be valid for the tender validity period."
                ),
                'table': {
                    'columns': ['Scope Item', 'Ex‑GST', 'GST', 'Incl‑GST', 'Total'],
                    'rows': [],
                },
            },
        ],
    })

    # Schedule 11 – Corporate Social Responsibility
    schedules.append({
        'schedule': 'Schedule 11',
        'title': 'Corporate Social Responsibility',
        'sections': [
            {
                'heading': 'CSR Policy / Initiatives',
                'content': "Describe your organisation’s corporate social responsibility policy or a relevant CSR initiative."
            },
        ],
    })

    # Schedule 12 – Sustainability
    schedules.append({
        'schedule': 'Schedule 12',
        'title': 'Sustainability',
        'sections': [
            {
                'heading': 'Sustainability Practices',
                'content': (
                    "Explain your organisation’s understanding of sustainability and outline the practices or initiatives you have in place "
                    "to support sustainable procurement and operations."
                ),
            },
        ],
    })

    # Schedule 13 – EEO & Fair Employment
    schedules.append({
        'schedule': 'Schedule 13',
        'title': 'Equal Employment Opportunity & Fair Employment',
        'sections': [
            {
                'heading': 'Policies & Evidence',
                'content': (
                    "Provide copies of your organisation’s policies and evidence of practices relating to equal employment opportunity and "
                    "fair employment. This may include recruitment and training policies, anti‑discrimination and harassment policies, "
                    "consultation and dispute resolution processes."
                ),
            },
            {
                'heading': 'Nominated Representative',
                'fields': ['Name', 'Position', 'Phone', 'Email'],
            },
            {
                'heading': 'Industrial Relations & Commitments',
                'content': (
                    "State any past breaches of wage or superannuation obligations and confirm rectification. Provide your commitments to "
                    "employing Aboriginal and Torres Strait Islander peoples, apprentices and trainees, and your acknowledgement of the "
                    "Industrial Relations Undertaking."
                ),
            },
        ],
    })

    # Schedule 14 – Work, Health & Safety (WHS)
    schedules.append({
        'schedule': 'Schedule 14',
        'title': 'Work, Health & Safety (WHS)',
        'sections': [
            {
                'heading': 'Acknowledgement of Council WHS Policy',
                'content': (
                    "Acknowledge that you have read Council’s WHS Policy and will comply with all WHS obligations applicable to the contract."
                ),
            },
            {
                'heading': 'Required WHS Evidence',
                'content': (
                    "Provide copies of your WHS manuals, policies and procedures; descriptions of WHS responsibilities and consultation processes; "
                    "sample checklists and inspection forms; records of WHS incidents and corrective actions; training records; risk assessments/" 
                    "SWMS; registers and SDS; plant and equipment maintenance records; permit‑to‑work samples; and a site‑specific WHS plan "
                    "for a similar project."
                ),
            },
            {
                'heading': 'Chain of Responsibility (CoR)',
                'content': (
                    "If transport of goods is involved, provide evidence of your Chain of Responsibility compliance, including a CoR policy, risk register, KPIs, training records, fleet maintenance and diary records, and subcontractor pre‑engagement audits."
                ),
            },
            {
                'heading': 'Required WHS Forms',
                'content': (
                    "Attach the completed WHS Forms (Appendices 1–3) and WHS Policy (Appendix 4)."
                ),
            },
        ],
    })

    # Schedule 15 – Modern Slavery Questionnaire
    schedules.append({
        'schedule': 'Schedule 15',
        'title': 'Modern Slavery Questionnaire',
        'sections': [
            {
                'heading': 'Supplier Declarations',
                'content': (
                    "Provide details of whether your organisation is reporting under the Australian Modern Slavery Act. Attach any modern slavery "
                    "policies and describe your due diligence processes, training initiatives and supply chain risk assessments. List the countries "
                    "of manufacture for products or components relevant to this tender."
                ),
            },
        ],
    })

    # Schedule 16 – Acknowledgement of Addenda & Tenderer’s Declaration
    schedules.append({
        'schedule': 'Schedule 16',
        'title': 'Acknowledgement of Addenda & Tenderer’s Declaration',
        'sections': [
            {
                'heading': 'Addenda Acknowledgement',
                'table': {
                    'columns': ['Addendum No.', 'Date Issued', 'Title / Subject', 'Acknowledged (Y/N)'],
                    'rows': [],
                },
                'content': "List all addenda issued for this RFT and indicate acknowledgment."
            },
            {
                'heading': 'Declaration',
                'content': (
                    "I/We declare that we have received all addenda listed above, that our tender complies with all requirements of the "
                    "tender documents except as noted, that the information provided in all returnable schedules is true and correct, and "
                    "that our offer remains open for the tender validity period (e.g., 120 days or as specified)."
                ),
            },
        ],
    })

    doc['schedules'] = schedules

    # Appendices (WHS forms & policy).  Provide names and brief descriptions.
    doc['appendices'] = {
        'appendix_1': {'code': 'WHS051.5', 'title': 'Contractor WHS Code of Conduct', 'type': 'form'},
        'appendix_2': {'code': 'WHS051.11', 'title': 'Contractor Scope of Works & Requirements', 'type': 'form'},
        'appendix_3': {'code': 'WHS051.8', 'title': 'Subcontractor Statement', 'type': 'form'},
        'appendix_4': {'code': 'WHS POL 100', 'title': 'WHS Policy', 'type': 'information'},
    }

    return doc