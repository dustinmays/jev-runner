JEV_ASK = {
    "name": "jev_ask",
    "description": (
        "Ask TypeSafe's Jev model one or more fast, typed decision questions about "
        "a piece of context (the 'state'). Use this for quick routing, classification, "
        "or yes/no/uncertain calls instead of reasoning it out yourself in a full chat "
        "turn — it's cheaper and faster. Not for open-ended text generation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "The context/text Jev should evaluate.",
            },
            "questions": {
                "type": "object",
                "description": (
                    "Map of question_key -> question spec. Each spec has 'type' "
                    "('noul' for a Yes/No/Uncertain/Likely confidence score, or "
                    "'choice' for a category), 'instructions' (what to decide), "
                    "and for 'choice', a 'choices' array of allowed labels."
                ),
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["noul", "choice"]},
                        "instructions": {"type": "string"},
                        "choices": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["type", "instructions"],
                },
            },
        },
        "required": ["state", "questions"],
    },
}
