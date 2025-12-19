"""
YAML parsing and analysis utilities.
"""

import re


def get_multiline_indicator(line: str) -> str | None:
    """
    Detect and map YAML multiline scalar indicators to a descriptive name.
    Handles all combinations of |, >, +, -, and 1-9 indent levels.
    Returns: e.g., 'literal', 'folded_keep_indent_2', or 'invalid_...'
    """
    match = re.match(r"^\s*\w[\w\-\.]*\s*:\s*([>|][^\s#]*)", line)
    if not match:
        return None

    raw = match.group(1)

    # Invalid if multiple digits or unknown characters
    if re.search(r"\d{2,}", raw) or re.search(r"[^>|0-9+-]", raw):
        return f"invalid_{raw}"

    style = "literal" if raw.startswith("|") else "folded"
    chomping = None
    indent = None

    # Extract components
    chomp_match = re.search(r"[+-]", raw)
    indent_match = re.search(r"[1-9]", raw)

    if chomp_match:
        chomping = chomp_match.group(0)
    if indent_match:
        indent = indent_match.group(0)

    # Build result
    name = style
    if chomping == "+":
        name += "_keep"
    elif chomping == "-":
        name += "_strip"
    if indent:
        name += f"_indent_{indent}"

    return name


def get_task_comments(file_path: str) -> list[dict[str, str]]:
    """
    Extracts comments for Ansible tasks.
    - For any named task (block or regular), uses any immediately preceding comments.
    - A blank line between a comment and the next task (or its direct comments)
      will prevent the earlier comment from being associated with that task.
    - Ignores comments not immediately preceding a named task due to other
      intervening non-comment lines.
    - Handles task names containing '#' if they are quoted, while still removing
      actual inline comments.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    output_task_comments = []
    # This list will hold comment lines gathered immediately before a potential task.
    candidate_comments = []

    for line_content in lines:
        stripped_line = line_content.strip()

        if stripped_line.startswith("#"):
            # Collect comments that might belong to the next task
            candidate_comments.append(stripped_line[1:].strip())
        elif stripped_line.startswith("- name:"):
            # This line defines a task. Process it and its collected candidate_comments.
            try:
                # Get the entire string part after "- name:"
                task_name_value_and_inline_comment = stripped_line.split(":", 1)[1]

                # Robustly find the first '#' that is NOT within quotes
                # to separate the actual task name value from a true inline comment.
                in_single_quote = False
                in_double_quote = False
                name_part_end_index = len(task_name_value_and_inline_comment)

                for k, char_code in enumerate(task_name_value_and_inline_comment):
                    # Basic quote state machine (doesn't handle escaped quotes within quotes)
                    if char_code == "'" and (
                        k == 0 or task_name_value_and_inline_comment[k - 1] != "\\"
                    ):
                        in_single_quote = not in_single_quote
                    elif char_code == '"' and (
                        k == 0 or task_name_value_and_inline_comment[k - 1] != "\\"
                    ):
                        in_double_quote = not in_double_quote
                    elif (
                        char_code == "#" and not in_single_quote and not in_double_quote
                    ):
                        name_part_end_index = k  # Found start of a true inline comment
                        break

                task_name_raw = task_name_value_and_inline_comment[
                    :name_part_end_index
                ].strip()

            except IndexError:
                # Malformed - name: line, skip
                candidate_comments = []  # Reset comments
                continue

            # Clean task name (remove surrounding quotes if they match)
            if (task_name_raw.startswith("'") and task_name_raw.endswith("'")) or (
                task_name_raw.startswith('"') and task_name_raw.endswith('"')
            ):
                task_name = task_name_raw[1:-1]
            else:
                task_name = task_name_raw

            # For markdown compatibility
            task_name = task_name.replace("|", "¦")

            comment_to_assign = ""
            if candidate_comments:
                # Assign all collected candidate_comments, joined by newline
                comment_to_assign = "\n".join(candidate_comments)

            if comment_to_assign:  # Only add if there's a comment
                output_task_comments.append(
                    {"task_name": task_name, "task_comments": comment_to_assign}
                )

            candidate_comments = []  # Reset for the next task

        elif not stripped_line:  # An empty line
            # An empty line always breaks the contiguity of comments for the next task.
            candidate_comments = []

        else:  # Any other type of line (e.g., module call, different list item)
            # These lines break the contiguity of comments leading to a task name.
            candidate_comments = []

    return output_task_comments


def get_task_line_numbers(file_path):
    """
    Get line numbers for tasks in an Ansible YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary mapping task names to line numbers
    """
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    tasks_lines = {}
    for idx, line in enumerate(lines):
        stripped_line = line.strip()

        if stripped_line.startswith("- name:"):
            task_name = (
                stripped_line.replace("- name:", "")
                .split("#")[0]
                .strip()
                .replace("|", "¦")
                .replace("'", "")
                .replace('"', "")
            )
            tasks_lines[task_name] = idx + 1

    return tasks_lines


def get_task_line_ranges(file_path):
    """
    Get line number ranges (start, end) for each task in an Ansible YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        List of tuples (start_line, end_line) in task order

    Example:
        >>> ranges = get_task_line_ranges('tasks/main.yml')
        >>> ranges
        [(1, 5), (6, 12), (13, 15)]
    """
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    task_ranges = []
    current_task_start = None

    for idx, line in enumerate(lines):
        stripped_line = line.strip()

        if stripped_line.startswith("- name:"):
            # If we were tracking a previous task, end it
            if current_task_start is not None:
                task_ranges.append(
                    (current_task_start, idx)
                )  # End at line before this one

            # Start tracking new task (1-indexed)
            current_task_start = idx + 1

    # Close the last task if one is open
    if current_task_start is not None:
        task_ranges.append((current_task_start, len(lines)))

    return task_ranges
