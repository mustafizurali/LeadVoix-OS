import re
from typing import Tuple, Optional


def normalize_phone(raw_phone: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes a raw phone string according to the LeadVoix OS phone policy:
    1. Preserves raw phone string (handled by caller).
    2. Parses extensions separately (e.g., 'ext 123', 'x45', '#101').
    3. Never guesses missing country codes (no assumption of +1 or any other prefix).
    4. Distinguishes syntactically plausible international strings (starts with '+',
       valid non-zero country code, 7-15 digits total) from national/domestic digits.
    5. Invalid, short (< 7 digits), over-length (> 15 digits), or ambiguous numbers remain NULL.
    6. Does not guarantee carrier/HLR validity (requires external lookup).

    Returns:
        (phone_normalized, phone_extension)
    """
    if not raw_phone:
        return None, None

    raw_phone_str = str(raw_phone).strip()
    if not raw_phone_str:
        return None, None

    # Step 1: Extract extension if present
    # Matches patterns like: ext 123, ext. 123, x123, x 123, #123
    ext_pattern = re.compile(r'(?i)(?:ext\.?|x|#)\s*([0-9]{1,10})\b')
    ext_match = ext_pattern.search(raw_phone_str)

    extension: Optional[str] = None
    if ext_match:
        extension = ext_match.group(1)
        # Strip extension part from the main number string
        main_part = raw_phone_str[:ext_match.start()].strip()
    else:
        main_part = raw_phone_str

    if not main_part:
        return None, extension

    # Step 2: Check for explicit international leading '+'
    has_leading_plus = main_part.startswith("+")

    # Extract all digits
    digits = re.sub(r'[^0-9]', '', main_part)

    # Step 3: Validate digit count (ITU-T E.164 allows 7 to 15 digits)
    if len(digits) < 7 or len(digits) > 15:
        # Invalid or ambiguous (e.g. shortcodes like '911', '101', or text without enough digits)
        return None, extension

    # Step 4: Validate international structure if leading '+' was present
    if has_leading_plus:
        if digits.startswith("0"):
            # ITU-T E.164 country codes cannot start with 0
            return None, extension
        # Syntactically plausible international format
        return f"+{digits}", extension

    # Step 5: Domestic / National digits without guessing country code
    # We do NOT prepend '+1' or any country code
    return digits, extension
