"""
XML Parser Module for SIH26146 Data Ingestion
Parses raw XML files and strings containing blockchain transactions or network events
into standard Python dictionaries suitable for downstream schema validation.
Runs 100% locally and offline without external dependencies.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Union


def parse_xml_to_dicts(xml_input: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Parses an XML string or file path into a list of dictionaries.
    Supports root containers such as <records>, <transactions>, <events>, <BlockchainTxns>, <NetworkEvents>
    with child elements representing individual records.
    """
    if isinstance(xml_input, Path) or (isinstance(xml_input, str) and (xml_input.endswith(".xml") or "/" in xml_input or "\\" in xml_input) and Path(xml_input).exists()):
        tree = ET.parse(xml_input)
        root = tree.getroot()
    elif isinstance(xml_input, str):
        root = ET.fromstring(xml_input.strip())
    else:
        raise ValueError(f"Unsupported XML input type: {type(xml_input)}")

    records: List[Dict[str, Any]] = []

    # Iterate through direct child elements of root
    for child in root:
        rec: Dict[str, Any] = {}
        # Also copy XML element attributes if any
        for k, v in child.attrib.items():
            rec[k] = v

        for field in child:
            tag = field.tag
            text = (field.text or "").strip()

            # Handle list elements with sub-items (e.g. <input_addresses><address>...</address></input_addresses>)
            sub_children = list(field)
            if sub_children:
                rec[tag] = [sub.text.strip() for sub in sub_children if sub.text]
            else:
                rec[tag] = text

        records.append(rec)

    return records
