import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from docsible import constants

logger = logging.getLogger(__name__)


def extract_task_name_from_module(task: Dict[str, Any], task_index: int = 0) -> str:
    """Extract a meaningful task name from the task dict when 'name' is not provided.

    Uses the module name or action (include_role, import_tasks, etc.) to create
    a descriptive name instead of "Unnamed_task_X".

    Args:
        task: Task dictionary
        task_index: Index of the task (used as fallback)

    Returns:
        A descriptive task name

    Example:
        >>> task = {'apt': {'name': 'nginx'}}
        >>> extract_task_name_from_module(task, 0)
        'apt (task 0)'
    """
    # If task has a name, return it
    if 'name' in task and task['name']:
        return task['name']

    # List of common task keys that aren't modules
    non_module_keys = {
        'name', 'when', 'tags', 'notify', 'register', 'changed_when',
        'failed_when', 'ignore_errors', 'delegate_to', 'run_once',
        'become', 'become_user', 'vars', 'loop', 'with_items',
        'until', 'retries', 'delay', 'check_mode', 'diff', 'any_errors_fatal',
        'environment', 'no_log', 'throttle', 'timeout', 'block', 'rescue', 'always'
    }

    # Check for include/import tasks first (these are special)
    include_import_keys = [
        'include_tasks', 'import_tasks', 'include_role', 'import_role',
        'ansible.builtin.include_tasks', 'ansible.builtin.import_tasks',
        'ansible.builtin.include_role', 'ansible.builtin.import_role',
        'include', 'import_playbook'
    ]

    for key in include_import_keys:
        if key in task:
            value = task[key]
            # Extract the file/role name
            if isinstance(value, dict):
                target = value.get('name') or value.get('file') or value.get('role') or str(value)
            else:
                target = str(value)

            # Clean up the key name (remove ansible.builtin. prefix)
            clean_key = key.replace('ansible.builtin.', '')
            return f"{clean_key}: {target}"

    # Check for block (block has special structure)
    if 'block' in task and isinstance(task.get('block'), list):
        return "block"

    # Find the module being used (first key that's not in non_module_keys)
    for key in task.keys():
        if key not in non_module_keys:
            # Found the module
            module_name = key.replace('ansible.builtin.', '')  # Clean up FQCN

            # Try to get a meaningful parameter from the module
            module_params = task[key]
            if isinstance(module_params, dict):
                # Common parameters that give context
                context_keys = ['name', 'path', 'dest', 'src', 'pkg', 'package', 'service', 'key', 'repo']
                for context_key in context_keys:
                    if context_key in module_params:
                        context_value = str(module_params[context_key])[:30]  # Limit length
                        return f"{module_name}: {context_value}"

            # Just return the module name
            return module_name

    # Fallback to unnamed with index
    return f"unnamed_task_{task_index}"


def sanitize_for_mermaid_id(text: str) -> str:
    """Sanitize text to create a valid Mermaid diagram node ID.

    Replaces pipes with underscores and removes non-alphanumeric characters
    (except French accents).

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use as Mermaid node ID

    Example:
        >>> sanitize_for_mermaid_id("Install | nginx-1.0")
        'Install___nginx_1_0'
    """
    text = text.replace("|", "_")
    # Allowing a-zA-Z0-9 as well as French accents
    return re.sub(r'[^a-zA-Z0-9À-ÿ]', '_', text)


def break_text(text: str, max_length: int = 50) -> str:
    """Break long text into multiple lines for better display in diagrams.

    Splits text at word boundaries to fit within max_length and joins with HTML <br> tags.

    Args:
        text: Text to break into lines
        max_length: Maximum length per line (default: 50)

    Returns:
        Text with <br> tags inserted for line breaks

    Example:
        >>> break_text("This is a very long text that needs wrapping", 20)
        'This is a very long<br>text that needs<br>wrapping'
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + len(current_line) > max_length:
            lines.append(' '.join(current_line))
            current_length = 0
            current_line = []
        current_line.append(word)
        current_length += len(word)
    if current_line:
        lines.append(' '.join(current_line))
    return '<br>'.join(lines)


def sanitize_for_title(text: str) -> str:
    """Sanitize text for use as diagram title.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into multiple lines if needed.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized and formatted text, or "cannot handle" if error occurs

    Example:
        >>> sanitize_for_title("Install Package: nginx-1.0")
        'install package nginx 1 0'
    """
    # Allowing a-z0-9 as well as French accents, and converting to lower case
    try:
        sanitized_text = re.sub(r'[^a-z0-9À-ÿ]', ' ', text.lower())
        return break_text(sanitized_text)
    except Exception as e:
        logger.warning(f"Failed to sanitize title '{text}': {e}")
        return "cannot handle"


def sanitize_for_condition(text: str, max_length: int = 50) -> str:
    """Sanitize conditional expression for display in diagrams.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into lines at max_length.

    Args:
        text: Conditional expression to sanitize
        max_length: Maximum length per line (default: 50)

    Returns:
        Sanitized and formatted conditional text

    Example:
        >>> sanitize_for_condition("ansible_os_family == 'RedHat'")
        'ansible os family redhat'
    """
    sanitized_text = re.sub(r'[^a-z0-9À-ÿ]', ' ', text.lower())
    return break_text(sanitized_text, max_length)


def process_tasks(
    tasks: List[Dict[str, Any]],
    last_node: str,
    mermaid_data: str,
    parent_node: Optional[str] = None,
    level: int = 0,
    in_rescue_block: bool = False
) -> Tuple[str, str]:
    """Process Ansible tasks and generate Mermaid diagram data.

    Recursively processes tasks including blocks, rescue, and always sections
    to build a flowchart representation.

    Args:
        tasks: List of task dictionaries to process
        last_node: ID of the previous node in the diagram
        mermaid_data: String accumulating Mermaid diagram syntax
        parent_node: ID of parent node (for nested blocks)
        level: Nesting level (for indentation/formatting)
        in_rescue_block: Whether currently processing rescue tasks

    Returns:
        Tuple of (last_node_id, mermaid_diagram_string)

    Example:
        >>> tasks = [{'name': 'Install nginx', 'apt': {'name': 'nginx'}}]
        >>> last_node, diagram = process_tasks(tasks, 'start', '')
        >>> print(last_node)
        'Install_nginx0'
    """
    for i, task in enumerate(tasks):
        has_rescue = False
        task_name = extract_task_name_from_module(task, i)
        task_module_include_tasks = task.get(
            "ansible.builtin.include_tasks") or task.get("include_tasks", False)
        task_module_import_tasks = task.get(
            "ansible.builtin.import_tasks") or task.get("import_tasks", False)
        task_module_import_playbook = task.get(
            "ansible.builtin.import_playbook") or task.get("import_playbook", False)
        task_module_include_role = task.get(
            "ansible.builtin.include_role") or task.get("include_role", False)
        task_module_import_role = task.get(
            "ansible.builtin.import_role") or task.get("import_role", False)
        task_module_include_vars = task.get(
            "ansible.builtin.include_vars") or task.get("include_vars", False)
        when_condition = task.get("when", False)
        block = task.get("block", False)
        rescue = task.get("rescue", False)
        task_name = re.sub(r"{{\s*(\w+)\s*}}", r"\1", task_name)
        sanitized_task_name = sanitize_for_mermaid_id(f"{task_name}{i}")
        sanitized_task_title = sanitize_for_title(task_name)
        if when_condition:
            if isinstance(when_condition, list):
                when_condition = " AND ".join(when_condition)
            sanitized_when_condition = f"**{sanitize_for_condition(str(when_condition)).strip()}**"
            if 'When:' not in sanitized_task_title:
                sanitized_task_title += f'<br>When: {sanitized_when_condition}'
        if block:
            block_start_node = sanitized_task_name + f'_block_start_{level}'
            mermaid_data += f'\n  {last_node}-->|Block Start| {block_start_node}[[{sanitized_task_title}]]:::block'
            last_node, mermaid_data = process_tasks(
                block, block_start_node, mermaid_data, block_start_node, level + 1, in_rescue_block=False)
            if rescue:
                has_rescue = True
                rescue_start_node = sanitized_task_name + \
                    f'_rescue_start_{level}'
                mermaid_data += f'\n  {last_node}-->|Rescue Start| {rescue_start_node}[{sanitized_task_title}]:::rescue'
                last_node, mermaid_data = process_tasks(
                    rescue, rescue_start_node, mermaid_data, block_start_node, level + 1, in_rescue_block=True)
                end_label = "End of Rescue Block"
                mermaid_data += f'\n  {last_node}-.->|{end_label}| {block_start_node}'
        elif rescue:
            rescue_start_node = sanitized_task_name + f'_rescue_start_{level}'
            mermaid_data += f'\n  {last_node}-->|Rescue Start| {rescue_start_node}[{sanitized_task_title}]:::rescue'
            last_node, mermaid_data = process_tasks(
                rescue, rescue_start_node, mermaid_data, parent_node, level + 1, in_rescue_block=True)
            end_label = "End of Rescue Block"
            mermaid_data += f'\n  {last_node}-.->|{end_label}| {parent_node}'
        else:

            if task_module_include_tasks:
                if isinstance(task_module_include_tasks, dict):
                    check_style_included_tasks = task_module_include_tasks.get(
                        'file', task_module_include_tasks)
                else:
                    check_style_included_tasks = task_module_include_tasks
                sanitized_include_tasks_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_included_tasks}_{i}")
                sanitized_include_tasks_title = sanitize_for_title(
                    f"{check_style_included_tasks}")
                mermaid_data += f'\n  {last_node}-->|Include task| {sanitized_include_tasks_name}[{sanitized_task_title}<br>include_task: {sanitized_include_tasks_title}]:::includeTasks'
                last_node = sanitized_include_tasks_name

            elif task_module_import_tasks:
                if isinstance(task_module_import_tasks, dict):
                    check_style_imported_tasks = task_module_import_tasks.get(
                        'file', task_module_import_tasks)
                else:
                    check_style_imported_tasks = task_module_import_tasks
                sanitized_imported_tasks_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_imported_tasks}_{i}")
                sanitized_imported_tasks_title = sanitize_for_title(
                    f"{check_style_imported_tasks}")
                mermaid_data += f'\n  {last_node}-->|Import task| {sanitized_imported_tasks_name}[/{sanitized_task_title}<br>import_task: {sanitized_imported_tasks_title}/]:::importTasks'
                last_node = sanitized_imported_tasks_name

            elif task_module_import_playbook:
                if isinstance(task_module_import_playbook, dict):
                    check_style_import_playbook = task_module_import_playbook.get(
                        'file', task_module_import_playbook)
                else:
                    check_style_import_playbook = task_module_import_playbook
                sanitized_import_playbook_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_import_playbook}_{i}")
                sanitized_import_playbook_title = sanitize_for_title(
                    f"{check_style_import_playbook}")
                mermaid_data += f'\n  {last_node}-->|Import playbook| {sanitized_import_playbook_name}[/{sanitized_task_title}<br>import_playbook: {sanitized_import_playbook_title}/]:::importPlaybook'
                last_node = sanitized_import_playbook_name

            elif task_module_include_role:
                if isinstance(task_module_include_role, dict):
                    check_style_include_role = task_module_include_role.get(
                        'name', task_module_include_role)
                else:
                    check_style_include_role = task_module_include_role
                sanitized_include_role_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_include_role}_{i}")
                sanitized_include_role_title = sanitize_for_title(
                    check_style_include_role)
                mermaid_data += f'\n  {last_node}-->|Include role| {sanitized_include_role_name}({sanitized_task_title}<br>include_role: {sanitized_include_role_title}):::includeRole'
                last_node = sanitized_include_role_name

            elif task_module_import_role:
                if isinstance(task_module_import_role, dict):
                    check_style_import_role = task_module_import_role.get(
                        'name', task_module_import_role)
                else:
                    check_style_import_role = task_module_import_role
                sanitized_import_role_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_import_role}_{i}")
                sanitized_import_role_title = sanitize_for_title(
                    check_style_import_role)
                mermaid_data += f'\n  {last_node}-->|Import role| {sanitized_import_role_name}([{sanitized_task_title}<br>import_role: {sanitized_import_role_title}]):::importRole'
                last_node = sanitized_import_role_name

            elif task_module_include_vars:
                if isinstance(task_module_include_vars, dict):
                    check_style_include_vars = task_module_include_vars.get(
                        'file', False) or task_module_include_vars.get('dir', task_module_include_vars)
                else:
                    check_style_include_vars = task_module_include_vars
                sanitized_include_vars_name = sanitize_for_mermaid_id(
                    f"{task_name}_{check_style_include_vars}_{i}")
                sanitized_include_vars_title = sanitize_for_title(
                    check_style_include_vars)
                mermaid_data += f'\n  {last_node}-->|Include vars| {sanitized_include_vars_name}[{sanitized_task_title}<br>include_vars: {sanitized_include_vars_title}]:::includeVars'
                last_node = sanitized_include_vars_name

            else:
                mermaid_data += f'\n  {last_node}-->|Task| {sanitized_task_name}[{sanitized_task_title}]:::task'
                last_node = sanitized_task_name

    if parent_node and not in_rescue_block and not has_rescue:
        end_label = "End of Block"
        mermaid_data += f'\n  {last_node}-.->|{end_label}| {parent_node}'

    return last_node, mermaid_data


def generate_mermaid_playbook(playbook: List[Dict[str, Any]]) -> str:
    """Generate Mermaid flowchart diagram from Ansible playbook.

    Creates a flowchart representation of playbook structure including
    hosts, roles, and tasks.

    Args:
        playbook: List of play dictionaries

    Returns:
        Mermaid diagram as string

    Example:
        >>> playbook = [{'hosts': 'webservers', 'tasks': [...]}]
        >>> diagram = generate_mermaid_playbook(playbook)
        >>> print(diagram[:15])
        'flowchart TD'
    """
    mermaid_data = "flowchart TD"
    for play in playbook:
        hosts = play.get("hosts", "UndefinedHost")
        tasks = play.get("tasks", [])
        roles = play.get("roles", [])
        if not isinstance(hosts, list):
            hosts = [hosts]
        sanitized_hosts = []
        for host in hosts:
            host = re.sub(r"{{\s*(\w+)\s*}}", r"\1", host)
            host = sanitize_for_mermaid_id(host)
            sanitized_hosts.append(host)
        sanitized_hosts = ", ".join(sanitized_hosts)
        sanitized_hosts = "hosts[" + sanitized_hosts + "]"
        last_node = sanitized_hosts
        if roles:
            for i, role in enumerate(roles):
                role_name = role["role"] if isinstance(role, dict) else role
                role_name = role_name if role_name else f"Unnamed_role_{i}"
                role_name = re.sub(r"{{\s*(\w+)\s*}}", r"\1", role_name)
                sanitized_role_name = sanitize_for_mermaid_id(role_name)
                sanitized_role_title = sanitize_for_title(role_name)
                mermaid_data += f'\n  {last_node}-->|Role| {sanitized_role_name}[{sanitized_role_title}]'
                last_node = sanitized_role_name
        last_node, mermaid_data = process_tasks(tasks, last_node, mermaid_data)
    return mermaid_data


def generate_mermaid_role_tasks_per_file(tasks_per_file: List[Dict[str, Any]]) -> Dict[str, str]:
    """Generate Mermaid diagrams for each task file in a role.

    Creates separate flowchart diagrams for each task file.

    Args:
        tasks_per_file: List of dicts with 'file' and 'mermaid' (task list) keys

    Returns:
        Dictionary mapping task file names to Mermaid diagram strings

    Example:
        >>> tasks_info = [{'file': 'main.yml', 'mermaid': [{'name': 'Task 1'}]}]
        >>> diagrams = generate_mermaid_role_tasks_per_file(tasks_info)
        >>> 'main.yml' in diagrams
        True
    """
    mermaid_codes = {}
    for task_info in tasks_per_file:
        task_file = task_info['file']
        tasks = task_info['mermaid']
        mermaid_data = """
                        flowchart TD
                        Start
                        classDef block stroke:#3498db,stroke-width:2px;
                        classDef task stroke:#4b76bb,stroke-width:2px;
                        classDef includeTasks stroke:#16a085,stroke-width:2px;
                        classDef importTasks stroke:#34495e,stroke-width:2px;
                        classDef includeRole stroke:#2980b9,stroke-width:2px;
                        classDef importRole stroke:#699ba7,stroke-width:2px;
                        classDef includeVars stroke:#8e44ad,stroke-width:2px;
                        classDef rescue stroke:#665352,stroke-width:2px;
                    """
        last_node = "Start"
        last_node, mermaid_data = process_tasks(tasks, last_node, mermaid_data)
        mermaid_data += f'\n  {last_node}-->End'
        mermaid_codes[task_file] = mermaid_data

    return mermaid_codes
