import re
from typing import Any, Dict, List

NUM = r"(?:\d+(?:\.\d+)?)"

def _findall_lines(text: str, header_regex: str, stop_regex: str) -> List[str]:
    lines = text.splitlines()
    out, capture = [], False
    hdr = re.compile(header_regex, re.I)
    stp = re.compile(stop_regex, re.I)
    for ln in lines:
        if not capture and hdr.search(ln):
            capture = True
            continue
        if capture and stp.search(ln):
            break
        if capture:
            out.append(ln)
    return [l.rstrip() for l in out]

def _harvest_numbered(lines: List[str]) -> List[str]:
    items = []
    for l in lines:
        if re.match(r"^\s*(?:\d+[\).]|[a-z][\).]|•|-)\s+", l.strip(), re.I) or l.strip():
            items.append(l.strip(" -•\t"))
    return [x for x in (s.strip() for s in items) if x]

def parse_spec(text: str) -> Dict[str, Any]:
    general = _harvest_numbered(_findall_lines(text, r"^\s*1\.\s*GENERAL REQUIREMENTS", r"^\s*2\.\s*DESCRIPTION OF WORKS"))
    each_ahu = _harvest_numbered(_findall_lines(text, r"2\.2\.1\s+Each AHU Plenums", r"2\.2\.2"))
    mech = _harvest_numbered(_findall_lines(text, r"2\.2\.2\s+Mechanical", r"2\.2\.3"))
    bmcs = _harvest_numbered(_findall_lines(text, r"2\.2\.3\s+Upgrade of Building Management Control System", r"2\.2\.4"))
    chiller_inst = _harvest_numbered(_findall_lines(text, r"2\.2\.4\s+Chiller installation", r"2\.2\.5"))
    water_tx = _harvest_numbered(_findall_lines(text, r"2\.2\.5\s+Water Treatment", r"2\.2\.6"))
    electrical = _harvest_numbered(_findall_lines(text, r"2\.2\.6\s+Electrical", r"2\.2\.7"))
    general_works = _harvest_numbered(_findall_lines(text, r"2\.2\.7\s+General", r"^\s*3\."))

    chillers = []
    m = re.search(r"(Carrier\s*61WG190A).*?(\b212\b)\s*kW", text, re.I)
    if m:
        chillers.append({"make_model": m.group(1).strip(), "count": 2, "heating_capacity_kw": float(m.group(2))})
    else:
        if re.search(r"water[-\s]cooled heat pump chiller", text, re.I):
            chillers.append({"make_model": None, "count": 2, "heating_capacity_kw": None})

    ec_fans_count = 8 if re.search(r"(?:eight|\(8\)|\b8\b)\s+EC\s+plug", text, re.I) else 0

    evaps = 4 if re.search(r"four\s*\(\s*4\s*\)\s*new evaporator coils", text, re.I) else 0
    conds = 2 if re.search(r"two\s*\(\s*2\s*\)\s*condenser coils", text, re.I) else 0
    hr_sets = 2 if re.search(r"two\s*\(\s*2\s*\)\s*sets of new run[-\s]around heat recovery coils\s*\(4 in total\)", text, re.I) else 0

    tests = _harvest_numbered(_findall_lines(text, r"^\s*10\.\s*TESTING\s*&\s*COMMISSIONING", r"^\s*11\.\s*WARRANTY"))
    warranty = int(re.search(r"Warrant(?:y|ies).*?(\d+)\s*months?", text, re.I).group(1)) if re.search(r"Warrant(?:y|ies).*?(\d+)\s*months?", text, re.I) else None
    maintenance = _harvest_numbered(_findall_lines(text, r"^\s*12\.\s*MAINTENANCE\s*&\s*SERVICE", r"^\s*13\."))

    whs = []
    import re as _re
    if _re.search(r"WorkSafe\s*NSW|SafeWork\s*NSW", text, re.I): whs.append("Comply with SafeWork NSW / Council WHS")
    if _re.search(r"PPE|personal protective equipment", text, re.I): whs.append("Provide PPE for all on-site workers")
    if _re.search(r"AS/?NZS\s*3000|AS3000", text, re.I): whs.append("Electrical work to AS/NZS 3000")
    if _re.search(r"ISO\s*9001", text, re.I): whs.append("Quality management to ISO 9001:2015")

    duty_flow = float(re.search(r"Duty\s*Flow\s*([0-9.]+)\s*L/S", text, re.I).group(1)) if re.search(r"Duty\s*Flow\s*([0-9.]+)\s*L/S", text, re.I) else None
    duty_head = float(re.search(r"Duty\s*Head\s*([0-9.]+)\s*M", text, re.I).group(1)) if re.search(r"Duty\s*Head\s*([0-9.]+)\s*M", text, re.I) else None
    voltage = re.search(r"(?:Power\s*Supply|Phase).*?(\d{3}/\d/\d{2})", text, re.I)
    voltage = voltage.group(1) if voltage else None
    pump_count = int(re.search(r"Number of Pumps\s*(\d+)", text, re.I).group(1)) if re.search(r"Number of Pumps\s*(\d+)", text, re.I) else None

    ec_table = []
    for row in re.findall(r"EF\s*\d-\d.*", text):
        vol = re.search(r"(\d{3,5})\s*(?:L/?s|\bLs\b)", row, re.I)
        stat = re.search(r"(\d{2,4})\s*Pa", row, re.I)
        volt = re.search(r"(?:3Ph/\s*\d{3}-\d{3}V|[23]Ph/\s*\d{3}-\d{3}V)", row, re.I)
        ec_table.append({
            "desc": row.strip(),
            "volume_ls": float(vol.group(1)) if vol else None,
            "static_pa": float(stat.group(1)) if stat else None,
            "voltage": volt.group(0) if volt else None
        })

    parsed = {
        "equipment": {
            "chillers": chillers,
            "ec_fans": {"count": ec_fans_count or None, "per_ahu": 4 if ec_fans_count==8 else None},
            "coils": {"evaporator_count": evaps or None, "condenser_count": conds or None, "heat_recovery_sets": hr_sets or None}
        },
        "bmcs": {"integration": bool(bmcs), "protocols": ["BACnet"] if re.search(r"BACnet|HLI", text, re.I) else []},
        "tests": [t for t in tests if t],
        "warranty_months": warranty,
        "maintenance": [m for m in maintenance if m],
        "whs": whs,
        "works_breakdown": {
            "decommission": [x for x in general if re.search(r"Removal|dispose|decommission", x, re.I)] + each_ahu,
            "mechanical": mech,
            "electrical": electrical,
            "ductwork": [x for x in general if re.search(r"duct", x, re.I)],
            "pipework": [x for x in general if re.search(r"pipe", x, re.I)],
            "cranage": [x for x in general if re.search(r"Cranage|Hoisting|lifting", x, re.I)] + chiller_inst,
            "general": general_works
        },
        "schedule_of_performances": {
            "pump": {"duty_flow_ls": duty_flow, "duty_head_m": duty_head, "voltage": voltage, "count": pump_count},
            "ec_fan": ec_table
        }
    }
    return parsed
