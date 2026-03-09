# annotated_role — docsible comment tags example

This role demonstrates how docsible comment tags (`# title:`, `# required:`, `# choices:`, `# description:`) are used in `defaults/main.yml` to populate the variable table in the generated README.

The role models a minimal nginx webserver configuration. It is not intended to be applied to a real host — its purpose is to show the full range of comment tag usage in a realistic context.

## What to look at

- `defaults/main.yml` — contains eight variables covering every combination:
  - all four tags present (`webserver_port`, `webserver_server_name`, `webserver_document_root`)
  - `title` + `required` only (`webserver_https_redirect`)
  - `title` + `required` + `choices` (`webserver_worker_processes`, `webserver_error_log_level`)
  - `title` + `required` only, no choices (`webserver_access_log`)
  - no tags at all, only an inline comment (`webserver_keepalive_timeout`)
- `tasks/main.yml` — each task has a `#` comment above it; these appear in the task Comments column.

## Try it

Run docsible against this role in dry-run mode to see the generated output without writing any files:

```bash
docsible document role --role examples/annotated_role --dry-run
```
