"""Fixtures for comparison tests."""

from pathlib import Path

import pytest


@pytest.fixture
def simple_role():
    """Path to simple role fixture."""
    return Path(__file__).parent.parent / "fixtures" / "simple_role"


@pytest.fixture
def complex_role():
    """Path to complex role fixture.

    Note: This fixture is actually categorized as MEDIUM (13 tasks).
    Use medium_role_fixture() or complex_role_fixture() for accurate testing.
    """
    return Path(__file__).parent.parent / "fixtures" / "complex_role"


@pytest.fixture
def medium_role_fixture(tmp_path):
    """Create a MEDIUM complexity role (11-25 tasks).

    Creates a role with:
    - 15 tasks across 3 task files
    - 2 handlers
    - Multiple variables
    - Some conditional logic
    - Basic includes

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "medium_role"
    role_path.mkdir()

    # Create tasks/main.yml with 8 tasks
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "main.yml").write_text("""---
# title: Main tasks
# description: Main installation and configuration

- name: Install required packages
  ansible.builtin.apt:
    name:
      - nginx
      - postgresql
      - redis
    state: present
    update_cache: yes
  when: ansible_os_family == "Debian"

- name: Create application directory
  ansible.builtin.file:
    path: /opt/myapp
    state: directory
    mode: '0755'
    owner: www-data
    group: www-data

- name: Copy configuration files
  ansible.builtin.template:
    src: "{{ item }}.j2"
    dest: "/etc/myapp/{{ item }}"
    mode: '0644'
  loop:
    - app.conf
    - database.conf
    - cache.conf
  notify: Restart application

- name: Include database setup tasks
  ansible.builtin.include_tasks: database.yml

- name: Include cache setup tasks
  ansible.builtin.include_tasks: cache.yml

- name: Enable and start services
  ansible.builtin.systemd:
    name: "{{ item }}"
    enabled: yes
    state: started
  loop:
    - nginx
    - postgresql
    - redis

- name: Configure firewall rules
  ansible.builtin.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - "80"
    - "443"
    - "5432"
  when: configure_firewall | default(true)

- name: Run health check
  ansible.builtin.uri:
    url: "http://localhost/health"
    status_code: 200
  retries: 3
  delay: 5
""")

    # Create tasks/database.yml with 4 tasks
    (tasks_dir / "database.yml").write_text("""---
# title: Database setup
# description: PostgreSQL database configuration

- name: Create database user
  community.postgresql.postgresql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"
    state: present

- name: Create application database
  community.postgresql.postgresql_db:
    name: "{{ db_name }}"
    owner: "{{ db_user }}"
    state: present

- name: Grant database privileges
  community.postgresql.postgresql_privs:
    database: "{{ db_name }}"
    roles: "{{ db_user }}"
    privs: ALL
    type: database

- name: Run database migrations
  ansible.builtin.command:
    cmd: /opt/myapp/migrate.sh
  changed_when: false
""")

    # Create tasks/cache.yml with 3 tasks
    (tasks_dir / "cache.yml").write_text("""---
# title: Cache setup
# description: Redis cache configuration

- name: Configure Redis
  ansible.builtin.lineinfile:
    path: /etc/redis/redis.conf
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
  loop:
    - regexp: '^maxmemory'
      line: 'maxmemory 256mb'
    - regexp: '^maxmemory-policy'
      line: 'maxmemory-policy allkeys-lru'
  notify: Restart redis

- name: Set Redis password
  ansible.builtin.lineinfile:
    path: /etc/redis/redis.conf
    regexp: '^requirepass'
    line: "requirepass {{ redis_password }}"
  notify: Restart redis

- name: Verify cache connectivity
  ansible.builtin.command:
    cmd: redis-cli -a {{ redis_password }} ping
  changed_when: false
""")

    # Create handlers
    handlers_dir = role_path / "handlers"
    handlers_dir.mkdir()
    (handlers_dir / "main.yml").write_text("""---
- name: Restart application
  ansible.builtin.systemd:
    name: myapp
    state: restarted

- name: Restart redis
  ansible.builtin.systemd:
    name: redis
    state: restarted
""")

    # Create defaults
    defaults_dir = role_path / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "main.yml").write_text("""---
db_user: myapp
db_name: myapp_production
db_password: changeme
redis_password: changeme
configure_firewall: true
app_port: 8080
app_workers: 4
app_timeout: 60
cache_ttl: 3600
max_connections: 100
""")

    # Create meta
    meta_dir = role_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "main.yml").write_text("""---
galaxy_info:
  author: Test Author
  description: Medium complexity web application deployment
  company: Example Corp
  license: MIT
  min_ansible_version: "2.9"
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
  galaxy_tags:
    - web
    - database
    - cache
dependencies: []
""")

    return role_path


@pytest.fixture
def complex_role_fixture(tmp_path):
    """Create a COMPLEX complexity role (26+ tasks).

    Creates a role with:
    - 30+ tasks across 5 task files
    - 4 handlers
    - Advanced features (includes, conditionals, loops, templates)
    - Multiple dependencies
    - Complex configuration

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "complex_role"
    role_path.mkdir()

    # Create tasks/main.yml with 10 tasks
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "main.yml").write_text("""---
# title: Main orchestration tasks
# description: Enterprise application deployment and configuration

- name: Validate prerequisites
  ansible.builtin.assert:
    that:
      - ansible_version.full is version('2.9', '>=')
      - ansible_os_family in ['Debian', 'RedHat']
      - app_env in ['development', 'staging', 'production']
    fail_msg: "Prerequisites not met"

- name: Detect system architecture
  ansible.builtin.set_fact:
    system_arch: "{{ ansible_architecture }}"
    is_production: "{{ app_env == 'production' }}"

- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"

- name: Install system dependencies
  ansible.builtin.package:
    name: "{{ system_packages }}"
    state: present
    update_cache: yes

- name: Create system users and groups
  ansible.builtin.include_tasks: users.yml

- name: Setup application infrastructure
  ansible.builtin.include_tasks: infrastructure.yml

- name: Configure load balancer
  ansible.builtin.include_tasks: loadbalancer.yml
  when: enable_loadbalancer | default(false)

- name: Setup database cluster
  ansible.builtin.include_tasks: database_cluster.yml

- name: Configure caching layer
  ansible.builtin.include_tasks: cache_cluster.yml

- name: Deploy application code
  ansible.builtin.include_tasks: deployment.yml

- name: Setup monitoring and logging
  ansible.builtin.include_tasks: monitoring.yml

- name: Configure backup strategy
  ansible.builtin.include_tasks: backup.yml

- name: Run smoke tests
  ansible.builtin.include_tasks: tests.yml
  when: run_tests | default(true)

- name: Register with service discovery
  ansible.builtin.uri:
    url: "{{ service_registry_url }}/register"
    method: POST
    body_format: json
    body:
      service: "{{ app_name }}"
      host: "{{ ansible_hostname }}"
      port: "{{ app_port }}"
      health_check: "http://{{ ansible_default_ipv4.address }}:{{ app_port }}/health"
    status_code: [200, 201]
  when: is_production
""")

    # Create tasks/infrastructure.yml with 6 tasks
    (tasks_dir / "infrastructure.yml").write_text("""---
# title: Infrastructure setup
# description: Core infrastructure provisioning

- name: Create application directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
    owner: "{{ app_user }}"
    group: "{{ app_group }}"
  loop:
    - "{{ app_root }}"
    - "{{ app_root }}/releases"
    - "{{ app_root }}/shared"
    - "{{ app_root }}/shared/config"
    - "{{ app_root }}/shared/logs"
    - "{{ app_root }}/shared/tmp"

- name: Deploy configuration templates
  ansible.builtin.template:
    src: "{{ item.src }}"
    dest: "{{ item.dest }}"
    mode: "{{ item.mode }}"
    owner: "{{ app_user }}"
    group: "{{ app_group }}"
  loop:
    - src: app.conf.j2
      dest: "{{ app_root }}/shared/config/app.conf"
      mode: '0644'
    - src: database.yml.j2
      dest: "{{ app_root }}/shared/config/database.yml"
      mode: '0600'
    - src: secrets.env.j2
      dest: "{{ app_root }}/shared/config/secrets.env"
      mode: '0600'
  notify: Restart application

- name: Setup log rotation
  ansible.builtin.template:
    src: logrotate.conf.j2
    dest: /etc/logrotate.d/{{ app_name }}
    mode: '0644'

- name: Configure systemd service
  ansible.builtin.template:
    src: systemd.service.j2
    dest: /etc/systemd/system/{{ app_name }}.service
    mode: '0644'
  notify:
    - Reload systemd
    - Restart application

- name: Setup SSL certificates
  ansible.builtin.include_tasks: ssl.yml
  when: enable_ssl | default(true)

- name: Configure network interfaces
  ansible.builtin.template:
    src: network.conf.j2
    dest: /etc/network/{{ app_name }}.conf
    mode: '0644'
  when: configure_network | default(false)
""")

    # Create tasks/database_cluster.yml with 5 tasks
    (tasks_dir / "database_cluster.yml").write_text("""---
# title: Database cluster setup
# description: High-availability PostgreSQL cluster

- name: Install PostgreSQL cluster packages
  ansible.builtin.apt:
    name:
      - postgresql
      - postgresql-contrib
      - python3-psycopg2
      - patroni
      - etcd
    state: present

- name: Configure Patroni for HA
  ansible.builtin.template:
    src: patroni.yml.j2
    dest: /etc/patroni/{{ app_name }}.yml
    mode: '0600'
  notify: Restart patroni

- name: Initialize database cluster
  ansible.builtin.command:
    cmd: patroni /etc/patroni/{{ app_name }}.yml
  when: inventory_hostname == groups['db_primary'][0]
  changed_when: false

- name: Create application database and users
  community.postgresql.postgresql_db:
    name: "{{ db_name }}"
    encoding: UTF8
    lc_collate: en_US.UTF-8
    lc_ctype: en_US.UTF-8
    template: template0
    state: present
  delegate_to: "{{ groups['db_primary'][0] }}"

- name: Setup database replication
  community.postgresql.postgresql_user:
    name: replicator
    password: "{{ replicator_password }}"
    role_attr_flags: REPLICATION
    state: present
  delegate_to: "{{ groups['db_primary'][0] }}"
""")

    # Create tasks/loadbalancer.yml with 5 tasks
    (tasks_dir / "loadbalancer.yml").write_text("""---
# title: Load balancer configuration
# description: HAProxy setup for traffic distribution

- name: Install HAProxy
  ansible.builtin.apt:
    name:
      - haproxy
      - hatop
    state: present

- name: Configure HAProxy
  ansible.builtin.template:
    src: haproxy.cfg.j2
    dest: /etc/haproxy/haproxy.cfg
    mode: '0644'
    validate: haproxy -c -f %s
  notify: Restart haproxy

- name: Setup backend health checks
  ansible.builtin.template:
    src: health_check.sh.j2
    dest: /usr/local/bin/{{ app_name }}_health_check.sh
    mode: '0755'

- name: Configure keepalived for failover
  ansible.builtin.template:
    src: keepalived.conf.j2
    dest: /etc/keepalived/keepalived.conf
    mode: '0644'
  when: enable_keepalived | default(false)
  notify: Restart keepalived

- name: Enable HAProxy stats page
  ansible.builtin.lineinfile:
    path: /etc/haproxy/haproxy.cfg
    line: "    stats enable"
    insertafter: "^listen stats"
  notify: Restart haproxy
""")

    # Create tasks/monitoring.yml with 5 tasks
    (tasks_dir / "monitoring.yml").write_text("""---
# title: Monitoring and observability
# description: Setup Prometheus, Grafana, and logging

- name: Install monitoring agents
  ansible.builtin.apt:
    name:
      - prometheus-node-exporter
      - filebeat
      - metricbeat
    state: present

- name: Configure Prometheus metrics endpoint
  ansible.builtin.template:
    src: prometheus.yml.j2
    dest: "{{ app_root }}/shared/config/prometheus.yml"
    mode: '0644'

- name: Setup log shipping to ELK
  ansible.builtin.template:
    src: filebeat.yml.j2
    dest: /etc/filebeat/filebeat.yml
    mode: '0644'
  notify: Restart filebeat

- name: Configure custom metrics
  ansible.builtin.template:
    src: metrics.conf.j2
    dest: "{{ app_root }}/shared/config/metrics.conf"
    mode: '0644'

- name: Setup alerting rules
  ansible.builtin.copy:
    src: alert_rules.yml
    dest: /etc/prometheus/rules/{{ app_name }}.yml
    mode: '0644'
  delegate_to: "{{ monitoring_server }}"
""")

    # Create handlers
    handlers_dir = role_path / "handlers"
    handlers_dir.mkdir()
    (handlers_dir / "main.yml").write_text("""---
- name: Restart application
  ansible.builtin.systemd:
    name: "{{ app_name }}"
    state: restarted
    daemon_reload: yes

- name: Reload systemd
  ansible.builtin.systemd:
    daemon_reload: yes

- name: Restart haproxy
  ansible.builtin.systemd:
    name: haproxy
    state: restarted

- name: Restart patroni
  ansible.builtin.systemd:
    name: patroni
    state: restarted

- name: Restart keepalived
  ansible.builtin.systemd:
    name: keepalived
    state: restarted

- name: Restart filebeat
  ansible.builtin.systemd:
    name: filebeat
    state: restarted
""")

    # Create defaults with many variables
    defaults_dir = role_path / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "main.yml").write_text("""---
# Application settings
app_name: enterprise_app
app_env: production
app_user: appuser
app_group: appgroup
app_root: /opt/{{ app_name }}
app_port: 8080
app_workers: 8
app_timeout: 120

# Database settings
db_name: enterprise_db
db_user: dbuser
db_password: "{{ vault_db_password }}"
replicator_password: "{{ vault_replicator_password }}"
db_pool_size: 20
db_timeout: 30

# Load balancer settings
enable_loadbalancer: true
enable_keepalived: true
lb_algorithm: roundrobin
health_check_interval: 5
health_check_timeout: 3

# SSL/TLS settings
enable_ssl: true
ssl_cert_path: /etc/ssl/certs/{{ app_name }}.crt
ssl_key_path: /etc/ssl/private/{{ app_name }}.key
ssl_protocols: ['TLSv1.2', 'TLSv1.3']

# Monitoring settings
monitoring_server: monitoring.example.com
metrics_port: 9090
enable_metrics: true
enable_logging: true
log_level: info
log_retention_days: 30

# Service registry
service_registry_url: http://consul.example.com:8500
enable_service_discovery: true

# Testing
run_tests: true
test_timeout: 300

# System packages (OS-specific)
system_packages:
  - curl
  - wget
  - git
  - build-essential
  - python3-pip
  - python3-venv

# Network configuration
configure_network: false
network_interface: eth0
network_mtu: 1500
""")

    # Create meta with dependencies
    meta_dir = role_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "main.yml").write_text("""---
galaxy_info:
  author: DevOps Team
  description: Enterprise-grade application deployment with HA and monitoring
  company: Enterprise Corp
  license: MIT
  min_ansible_version: "2.10"
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
    - name: Debian
      versions:
        - bullseye
  galaxy_tags:
    - enterprise
    - web
    - database
    - monitoring
    - loadbalancer
    - ha

dependencies:
  - role: geerlingguy.postgresql
    vars:
      postgresql_version: "14"
  - role: geerlingguy.nginx
    vars:
      nginx_worker_processes: "auto"
""")

    return role_path


@pytest.fixture
def minimal_role(tmp_path):
    """Create a truly minimal Ansible role for testing MinimalModeRule.

    Creates a role that satisfies MinimalModeRule criteria:
    - 3 tasks (< 5 threshold)
    - No handlers
    - No advanced features (includes, imports, roles)
    - Single task file
    - No dependencies

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "minimal_role"
    role_path.mkdir()

    # Create tasks directory with 3 simple tasks
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "main.yml").write_text("""---
- name: Install package
  ansible.builtin.package:
    name: nginx
    state: present

- name: Create directory
  ansible.builtin.file:
    path: /opt/app
    state: directory

- name: Copy config file
  ansible.builtin.copy:
    src: config.conf
    dest: /etc/app/config.conf
""")

    # Create defaults (optional)
    defaults_dir = role_path / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "main.yml").write_text("""---
app_name: myapp
""")

    # Create meta (required)
    meta_dir = role_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "main.yml").write_text("""---
galaxy_info:
  author: Test Author
  description: Minimal test role
  license: MIT
dependencies: []
""")

    # NO handlers directory - this is key for minimal mode!

    return role_path


@pytest.fixture
def many_files_role(tmp_path):
    """Create a role with 6+ task files to test graph generation threshold.

    Creates a role with:
    - 6 task files (triggers GraphDecisionRule complex logic)
    - Multiple includes (realistic structure)
    - No dependencies

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "many_files_role"
    role_path.mkdir()

    # Create tasks directory with 6 task files
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()

    # Create main.yml with includes
    (tasks_dir / "main.yml").write_text("""---
- name: Include setup tasks
  ansible.builtin.include_tasks: setup.yml

- name: Include config tasks
  ansible.builtin.include_tasks: config.yml

- name: Include deploy tasks
  ansible.builtin.include_tasks: deploy.yml

- name: Include monitor tasks
  ansible.builtin.include_tasks: monitor.yml

- name: Include cleanup tasks
  ansible.builtin.include_tasks: cleanup.yml
""")

    # Create 5 additional task files (total 6 files)
    for task_file in ["setup.yml", "config.yml", "deploy.yml", "monitor.yml", "cleanup.yml"]:
        (tasks_dir / task_file).write_text(f"""---
- name: Task in {task_file}
  ansible.builtin.debug:
    msg: "Running {task_file}"

- name: Another task in {task_file}
  ansible.builtin.debug:
    msg: "Second task in {task_file}"
""")

    # Create minimal meta for valid role
    meta_dir = role_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "main.yml").write_text("""---
galaxy_info:
  author: Test
  description: Test role with many task files
dependencies: []
""")

    return role_path


@pytest.fixture
def empty_role(tmp_path):
    """Create a minimal Ansible role structure for testing.

    Creates a role with:
    - tasks/main.yml with one task
    - defaults/main.yml with one variable
    - meta/main.yml with basic metadata

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "test_role"
    role_path.mkdir()

    # Create tasks
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()
    return role_path