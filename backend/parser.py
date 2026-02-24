

import re
from datetime import datetime
from typing import Optional

# ─── REGEX BASICS FOR BEGINNERS ────────────────────────
# A regex is a pattern that describes what text looks like.
#
# Key symbols used in this file:
#   \d     → any digit 0-9
#   \d{4}  → exactly 4 digits
#   \s     → any whitespace (space, tab)
#   \s+    → one or more whitespace characters
#   \S+    → one or more NON-whitespace characters
#   .+     → one or more of ANY character
#   \w+    → one or more word characters (letters, digits, _)
#   (...)  → capture group — we want this part
#   (?:...)→ non-capture group — we use this to group but don't want it
#   [abc]  → match a, b, or c
#   [^abc] → match anything EXCEPT a, b, or c
#   ?      → makes the previous item optional
#   |      → OR operator: (A|B) means A or B
#
# Why r'...' (raw strings)?
#   In normal strings, \n means newline, \t means tab.
#   In raw strings, \n is literally backslash-n.
#   Regex uses lots of backslashes, so ALWAYS use r'...'
#   to prevent Python from misreading them.
#
# re.match() vs re.search():
#   re.match()  → only checks from the START of the string
#   re.search() → checks ANYWHERE in the string
#   We use re.match() because our patterns must match
#   from the beginning of each log line.
# ───────────────────────────────────────────────────────


class LogParser:
    # We try the most specific patterns first.
    # App log has 4 identifiable fields — very specific.
    # Apache log format is tried last because its structure
    # is so different it won't accidentally match other formats.
    # Always go specific → general. Never general → specific.

    def __init__(self):
        # We compile patterns once in __init__ instead of
        # re-compiling on every call to parse_line().
        # For a file with 100,000 lines, this saves
        # compiling the same pattern 100,000 times.

        # PATTERN 1 — App log
        self.pattern1 = re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(ERROR|WARN|INFO|DEBUG)\s+(\S+)\s+-\s+(.+)')
        # Pattern 1 plain English:
        # (\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}) 
        #   → capture timestamp like "2024-12-01 03:17:44"
        #   → \d{4} = exactly 4 digits, \d{2} = exactly 2 digits
        # \s+ → one or more spaces (separator)
        # (ERROR|WARN|INFO|DEBUG) → capture the level word exactly
        # \s+ → spaces again
        # (\S+) → capture service name (no spaces allowed in service name)
        # \s+-\s+ → space, dash, space separator
        # (.+) → capture everything remaining as the message

        # PATTERN 2 — Syslog
        self.pattern2 = re.compile(r'(\w+\s+\d+\s+[\d:]+)\s+(\S+)\s+(\w+)(?:\[\d+\])?: (.+)')
        # Pattern 2 plain English:
        # (\w+\s+\d+\s+[\d:]+) 
        #   → capture date like "Dec  1 03:17:44"
        #   → \w+ = month name, \d+ = day, [\d:]+ = time digits and colons
        # \s+ → spaces
        # (\S+) → capture hostname like "prod-server-01"
        # \s+ → spaces
        # (\w+) → capture service name like "nginx"
        # (?:\[\d+\])? → optionally skip process ID like [1234]
        #   → ?: means non-capturing (we don't need the PID)
        #   → ? after the group means the whole thing is optional
        # : → colon separator
        # (.+) → capture everything remaining as the message

        # PATTERN 3 — Bracketed level
        self.pattern3 = re.compile(r'\[(ERROR|WARN|WARNING|INFO|DEBUG)\]\s+(.+)')
        # Pattern 3 plain English:
        # \[ → literal opening square bracket
        #   → we must escape it with \ because [ has special meaning in regex
        # (ERROR|WARN|WARNING|INFO|DEBUG) → capture one of these exact words
        # \] → literal closing square bracket (also escaped)
        # \s+ → one or more spaces after the bracket
        # (.+) → capture everything remaining as the message
        # Note: this pattern has no timestamp or service — 
        #        we set those to datetime.now() and "unknown"

        # PATTERN 4 — Apache/Nginx log
        self.pattern4 = re.compile(r'(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d+)')
        # Pattern 4 plain English:
        # (\S+) → capture IP address like "192.168.1.1"
        # \S+ \S+ → skip the two dashes: - -
        # \[([^\]]+)\] → capture date inside square brackets
        #   → [^\]]+ means "any character except ]" — stops at closing bracket
        # "(\S+) → opening quote then capture HTTP method like "GET"
        # (\S+) → capture URL path like "/api/users"
        # [^"]* → skip anything else inside the quotes (HTTP version etc)
        # " → closing quote
        # (\d+) → capture status code like 200 or 500
        # Note: we use the status code to determine level:
        #        500+ = ERROR, 400+ = WARN, everything else = INFO

    def parse_line(self, raw_line: str) -> dict:
        # Try patterns in the exact order specified: 1 → 2 → 3 → 4
        m = self.pattern1.match(raw_line)
        if m:
            ts_str = m.group(1)
            try:
                timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp = datetime.now()
            level = m.group(2).upper()
            service = m.group(3)
            message = m.group(4).strip()
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "host": "unknown",
                "raw_line": raw_line,
            }

        m = self.pattern2.match(raw_line)
        if m:
            timestamp = datetime.now()
            level = "INFO"
            service = m.group(3)
            message = m.group(4).strip()
            host = m.group(2)
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "host": host,
                "raw_line": raw_line,
            }

        m = self.pattern3.match(raw_line)
        if m:
            timestamp = datetime.now()
            level = m.group(1).upper()
            if level == "WARNING":
                level = "WARN"
            service = "unknown"
            message = m.group(2).strip()
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "host": "unknown",
                "raw_line": raw_line,
            }

        m = self.pattern4.match(raw_line)
        if m:
            timestamp = datetime.now()
            status = int(m.group(5))
            level = "ERROR" if status >= 500 else "WARN" if status >= 400 else "INFO"
            service = "web-server"
            message = f"{m.group(3)} {m.group(4)} → HTTP {status}"
            host = m.group(1)
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "host": host,
                "raw_line": raw_line,
            }

        # Default case
        return {
            "timestamp": datetime.now(),
            "level": "UNKNOWN",
            "service": "unrecognized",
            "message": raw_line.strip(),
            "host": "unknown",
            "raw_line": raw_line,
        }

    def parse_file(self, file_content: str) -> list[dict]:
        lines = file_content.splitlines()
        result = []
        count = 0
        for line in lines:
            if not line.strip():
                continue
            count += 1
            result.append(self.parse_line(line))
            if count % 1000 == 0:
                print(f"  Parsed {count} lines...")
        return result

"""
Testing parser:
[Pattern 1] Level:ERROR     Service:payment-svc      Msg:DB conn failed
[Pattern 1] Level:INFO      Service:auth-svc         Msg:User logged in
[Pattern 3] Level:WARN      Service:unknown          Msg:Memory usage above 80 p
[Pattern 3] Level:ERROR     Service:unknown          Msg:Disk space critically lo
[Default]   Level:UNKNOWN   Service:unrecognized     Msg:garbage line #### not a
parser.py OK ✅
"""


if __name__ == "__main__":
    from parser import LogParser

    p = LogParser()

    test_cases = [
        ('Pattern 1', '2024-12-01 03:17:44 ERROR payment-svc - DB conn failed'),
        ('Pattern 1', '2024-12-01 03:17:45 INFO auth-svc - User logged in'),
        ('Pattern 3', '[WARN] Memory usage above 80 percent'),
        ('Pattern 3', '[ERROR] Disk space critically low'),
        ('Default',   'garbage line #### not a real log @@'),
    ]

    print('Testing parser:')
    all_pass = True
    for expected_pattern, line in test_cases:
        result = p.parse_line(line)
        print(f'  [{expected_pattern}] Level:{result["level"]:<9} Service:{result["service"]:<16} Msg:{result["message"][:25]}')
        if result['level'] == 'UNKNOWN' and expected_pattern != 'Default':
            print(f'  ❌ FAIL: Expected pattern to match but got UNKNOWN')
            all_pass = False

    if all_pass:
        print('parser.py OK ✅')
    else:
        print('parser.py has errors ❌ — check the patterns above')

    # Apache test
    apache_line = '192.168.1.1 - - [01/Dec/2024:03:17:44 +0000] "GET /api HTTP/1.1" 500 1234'
    result = p.parse_line(apache_line)
    print('\nPattern 4 test:')
    print(f'  Level:   {result["level"]}')
    print(f'  Service: {result["service"]}')
    print(f'  Host:    {result["host"]}')
    print(f'  Message: {result["message"]}')

