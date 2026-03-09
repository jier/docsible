"""docsible scan — batch scan commands for collections and multi-role projects."""

import click

from .collection import scan_collection_cmd


@click.group(name="scan")
def scan_group() -> None:
    """Scan Ansible collections and multi-role projects."""


scan_group.add_command(scan_collection_cmd, name="collection")
