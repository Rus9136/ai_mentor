"""
JSON parsing utilities for AI responses.

Eliminates duplication between question and grading parsing.
"""

import json
import re
from typing import Any, List


def strip_markdown_code_blocks(response: str) -> str:
    """
    Remove markdown code blocks from response.

    Handles both ```json and plain ``` blocks.

    Args:
        response: Raw LLM response

    Returns:
        Cleaned response without markdown
    """
    response = response.strip()

    if not response.startswith("```"):
        return response

    lines = response.split("\n")
    json_lines = []
    in_block = False

    for line in lines:
        if line.startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            json_lines.append(line)

    return "\n".join(json_lines)


def parse_json_array(response: str) -> List[Any]:
    """
    Parse JSON array from LLM response.

    Handles markdown code blocks and extracts array from mixed text.

    Args:
        response: Raw LLM response

    Returns:
        Parsed list

    Raises:
        ValueError: If no valid JSON array found
    """
    cleaned = strip_markdown_code_blocks(response)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON array in response
        match = re.search(r'\[[\s\S]*\]', cleaned)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError("Could not find JSON array in response") from None

    if not isinstance(result, list):
        raise ValueError("Response is not a JSON array")

    return result


def parse_json_object(response: str) -> dict:
    """
    Parse JSON object from LLM response.

    Handles markdown code blocks and extracts object from mixed text.

    Args:
        response: Raw LLM response

    Returns:
        Parsed dict

    Raises:
        ValueError: If no valid JSON object found
    """
    cleaned = strip_markdown_code_blocks(response)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in response
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError("Could not find JSON in response") from None

    return result
