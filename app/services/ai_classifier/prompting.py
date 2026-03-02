from datetime import date

CLASSIFICATION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["essential", "non_essential", "emergency"],
        },
        "intent_label": {
            "type": "string",
            "enum": ["planned", "impulse", "na"],
        },
        "essentiality": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
        },
    },
    "required": ["category", "intent_label", "essentiality"],
    "additionalProperties": False,
}


def build_classification_prompt(txn_date: date, description: str, amount: float) -> str:
    return f"""
You are a strict financial transaction classifier.
Return ONLY valid JSON with exactly these keys:
- category: one of [\"essential\", \"non_essential\", \"emergency\"]
- intent_label: one of [\"planned\", \"impulse\", \"na\"]
- essentiality: integer in [0, 10]

Rules:
1) Category meaning:
   - essential: recurring survival or core living needs.
   - non_essential: discretionary spending.
   - emergency: urgent unplanned high-priority event.
2) If category is non_essential, intent_label MUST be planned or impulse.
3) If category is essential or emergency, intent_label MUST be \"na\".
4) essentiality scale:
   - 0 means pure luxury/avoidable.
   - 10 means survival-critical.
5) No extra keys, no explanations, no markdown.
6) Output must be a JSON object only. Do not wrap in backticks.

Transaction:
- date: {txn_date.isoformat()}
- description: {description}
- amount: {amount:.2f}
""".strip()
