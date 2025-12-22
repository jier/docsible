"Sinmplifcation of suggestion string for maintanability purposes"

class Suggestion:
    
    @staticmethod
    def complex_conditionals() -> str:
        return (
            "Simplify complex conditionals:\n\n"
            "**Option 1: Use intermediate facts**\n"
            "```yaml\n"
            "- name: Determine if action needed\n"
            "  set_fact:\n"
            '    should_run: "{{ (condition1) or (condition2) }}"\n'
            "\n"
            "- name: Your task\n"
            "  ...\n"
            "  when: should_run | bool\n"
            "```\n\n"
            "**Option 2: Split into separate files**\n"
            "```yaml\n"
            "# main.yml\n"
            "- include_tasks: debian_setup.yml\n"
            "  when: ansible_os_family == 'Debian'\n"
            "\n"
            "- include_tasks: redhat_setup.yml\n"
            "  when: ansible_os_family == 'RedHat'\n"
            "```\n\n"
            "**Option 3: Use block conditionals**\n"
            "```yaml\n"
            "- block:\n"
            "    - name: Task 1\n"
            "    - name: Task 2\n"
            "  when: complex_condition\n"
            "```"
        )
    
    @staticmethod
    def deep_include_chains() -> str:
        return (
            "Reduce include nesting:\n\n"
            "**Current structure:**\n"
            "```\n"
            "main.yml → file1.yml → file2.yml → file3.yml\n"
            "```\n\n"
            "**Flattened structure:**\n"
            "```yaml\n"
            "# main.yml\n"
            "- import_tasks: install.yml\n"
            "- import_tasks: configure.yml\n"
            "- import_tasks: services.yml\n"
            "```\n\n"
            "Keep hierarchy shallow (2-3 levels max) for easier debugging."
        )
    
    @staticmethod
    def excessive_set_fact() -> str:
        return (
            "Reduce set_fact usage:\n\n"
            "**1. Use role defaults/vars instead:**\n"
            "```yaml\n"
            "# defaults/main.yml\n"
            "computed_value: \"{{ base_value | default('default') }}\"\n"
            "```\n\n"
            "**2. Use vars at task level:**\n"
            "```yaml\n"
            "- name: Task that needs variable\n"
            "  debug:\n"
            '    msg: "{{ my_var }}"\n'
            "  vars:\n"
            '    my_var: "{{ complex_expression }}"\n'
            "```\n\n"
            "**3. Use Jinja2 filters directly:**\n"
            "```yaml\n"
            "# Instead of:\n"
            '- set_fact: upper_name="{{ name | upper }}"\n'
            '- debug: msg="{{ upper_name }}"\n'
            "\n"
            "# Just use:\n"
            '- debug: msg="{{ name | upper }}"\n'
            "```\n\n"
                            "Reserve set_fact for truly dynamic values that change during playbook execution."
        )