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


def _fix_json(text: str) -> str:
    """Fix common JSON issues from LLM responses."""
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Remove single-line comments
    text = re.sub(r'//[^\n]*', '', text)
    return text


def parse_json_array(response: str) -> List[Any]:
    """
    Parse JSON array from LLM response.

    Handles markdown code blocks, trailing commas, and extracts array from mixed text.

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
            extracted = match.group()
            try:
                result = json.loads(extracted)
            except json.JSONDecodeError:
                result = json.loads(_fix_json(extracted))
        else:
            raise ValueError("Could not find JSON array in response") from None

    if not isinstance(result, list):
        raise ValueError("Response is not a JSON array")

    return result


def parse_json_object(response: str) -> dict:
    """
    Parse JSON object from LLM response.

    Handles markdown code blocks, trailing commas, and extracts object from mixed text.

    Args:
        response: Raw LLM response

    Returns:
        Parsed dict

    Raises:
        ValueError: If no valid JSON object found
    """
    cleaned = strip_markdown_code_blocks(response)

    # Try direct parse first
    try:
        result = json.loads(cleaned)
        return result
    except json.JSONDecodeError:
        pass

    # Try extracting JSON object from text
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        extracted = match.group()
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
        # Try fixing common LLM JSON issues
        fixed = _fix_json(extracted)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    # Last resort: fix the full cleaned text
    fixed = _fix_json(cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        raise ValueError("Could not find valid JSON in response") from None
