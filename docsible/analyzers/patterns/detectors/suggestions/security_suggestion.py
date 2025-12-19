"Sinmplifcation of suggestion string for maintanability purposes"

class Suggestion:
    
    @staticmethod
    def exposed_secrets(var_type: str) -> str:
        return (
            "Protect sensitive data:\n\n"
            "**Option 1: Use ansible-vault**\n"
            "```bash\n"
            "# Encrypt the file\n"
            f"ansible-vault encrypt {var_type}/main.yml\n"
            "\n"
            "# Or encrypt individual variables\n"
            "ansible-vault encrypt_string 'secret_value' --name 'variable_name'\n"
            "```\n\n"
            "**Option 2: Use external secret management**\n"
            "```yaml\n"
            "# defaults/main.yml\n"
            "db_password: \"{{ lookup('env', 'DB_PASSWORD') }}\"\n"
            "api_token: \"{{ lookup('hashivault', 'secret/api_token') }}\"\n"
            "```\n\n"
            "**Option 3: Use group_vars with vault**\n"
            "```bash\n"
            "# Store secrets in encrypted group_vars\n"
            "ansible-vault create group_vars/production/vault.yml\n"
            "```\n\n"
            "Never commit plain-text secrets to version control!"
        )
    
    @staticmethod
    def missing_no_log() -> str:
        return (
            "Add no_log to prevent secret exposure:\n\n"
            "```yaml\n"
            "- name: Set database password\n"
            "  set_fact:\n"
            '    db_password: "{{ vault_db_password }}"\n'
            "  no_log: true  # ← Prevents logging to console/logs\n"
            "\n"
            "- name: Create user with password\n"
            "  user:\n"
            "    name: appuser\n"
            "    password: \"{{ user_password | password_hash('sha512') }}\"\n"
            "  no_log: true  # ← Prevents password in logs\n"
            "```\n\n"
            "Use no_log whenever:\n"
            "- Setting password variables\n"
            "- Calling APIs with tokens\n"
            "- Handling any sensitive data"
        )
    
    @staticmethod
    def insecure_permission() -> str:
        return (
            "Use appropriate file permissions:\n\n"
            "```yaml\n"
            "# For configuration files\n"
            "- name: Copy config\n"
            "  copy:\n"
            "    src: app.conf\n"
            "    dest: /etc/app.conf\n"
            "    mode: '0644'  # Owner: rw, Group: r, Others: r\n"
            "\n"
            "# For private keys/secrets\n"
            "- name: Copy SSL key\n"
            "  copy:\n"
            "    src: server.key\n"
            "    dest: /etc/ssl/private/server.key\n"
            "    mode: '0600'  # Owner: rw, Group: none, Others: none\n"
            "\n"
            "# For executable scripts\n"
            "- name: Copy script\n"
            "  copy:\n"
            "    src: script.sh\n"
            "    dest: /usr/local/bin/script.sh\n"
            "    mode: '0755'  # Owner: rwx, Group: rx, Others: rx\n"
            "```\n\n"
            "**Never use 0777 (world-writable) in production!**"
        )
    
    @staticmethod
    def shell_injection_risks() -> str:
        return (
            "Avoid shell injection:\n\n"
            "**Bad - Injection risk:**\n"
            "```yaml\n"
            "- name: Delete file\n"
            '  shell: "rm -rf {{ user_path }}"  # ← Dangerous!\n'
            "  # What if user_path = '/ --no-preserve-root'?\n"
            "```\n\n"
            "**Good - Use native modules:**\n"
            "```yaml\n"
            "- name: Delete file\n"
            "  file:\n"
            '    path: "{{ user_path }}"\n'
            "    state: absent\n"
            "  # Module handles escaping safely\n"
            "```\n\n"
            "**If shell is necessary - validate input:**\n"
            "```yaml\n"
            "- name: Validate path\n"
            "  assert:\n"
            "    that:\n"
            "      - user_path is match('^/safe/path/.*')\n"
            '    fail_msg: "Invalid path"\n'
            "\n"
            "- name: Delete file\n"
            '  shell: "rm -rf {{ user_path | quote }}"\n'
            "```\n\n"
            "Prefer Ansible modules over shell commands whenever possible."
        )