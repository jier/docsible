# Contributing Guidelines

## Introduction

Thank you for considering contributing to Docsible! We appreciate your effort and contributions can help the project grow and improve.

## How to Get Started

- **Fork the Repository**: Click on the "Fork" button at the top-right corner of the repository page on GitHub.
  
- **Clone the Repository**: After forking, clone your forked repository to your local machine.

    ```bash
    git clone https://github.com/[Your-Username]/docsible.git
    ```
  
- **Add Remote Repository**: Set up the upstream remote to keep your fork in sync with the original repository.

    ```bash
    git remote add upstream https://github.com/docsible/docsible.git
    ```

## CLI Content Control Flags

Docsible provides granular control over documentation content through CLI flags. These flags allow you to customize what sections appear in the generated documentation.

### Available Flags

| Flag | Description | Use Case |
|------|-------------|----------|
| `--no-vars` | Hide variable documentation (defaults, vars, argument_specs) | Focus on task flow and architecture |
| `--no-tasks` | Hide task lists and task details | Focus on variables and structure |
| `--no-diagrams` | Hide all Mermaid diagrams | For systems that don't render Mermaid |
| `--simplify-diagrams` | Show only high-level diagrams, hide detailed task flowcharts | Reduce visual complexity |
| `--no-examples` | Hide example playbook sections | Omit usage examples |
| `--no-metadata` | Hide role metadata, author, and license information | Omit publishing information |
| `--no-handlers` | Hide handlers section | When handlers aren't relevant |
| `--minimal` | Generate minimal documentation (enables all --no-* flags) | Create bare-minimum documentation |

### Usage Examples

```bash
# Generate standard documentation
docsible role --role ./my-role

# Hide only variables
docsible role --role ./my-role --no-vars

# Hide tasks but keep everything else
docsible role --role ./my-role --no-tasks

# Hide all diagrams
docsible role --role ./my-role --no-diagrams

# Show only high-level diagrams (hide detailed task flowcharts)
docsible role --role ./my-role --graph --simplify-diagrams

# Generate minimal documentation
docsible role --role ./my-role --minimal

# Combine multiple flags
docsible role --role ./my-role --no-vars --no-examples --graph

# Document entire collection with simplified diagrams
docsible role --collection ./my-collection --graph --simplify-diagrams
```

### Sequence Diagram Behavior

- **Default**: Full detailed task execution flow with all interactions
- **With `--minimal` or `--simplify-diagrams`**: Simplified diagrams showing task counts instead of individual task details
- This gives you control over the level of detail in sequence diagrams

### Template Support

All content control flags work with both:
- **Standard template**: Auto-generated documentation
- **Hybrid template**: Combines manual sections with auto-generated content

Both templates respect the same flags for consistent behavior.

## Workflow

1. **Sync Your Fork**: Before you start, always make sure your local repository is up-to-date with the upstream repository.

    ```bash
    git pull upstream main
    ```

2. **Create a Branch**: Create a new branch for each task, feature, or bugfix.

    ```bash
    git checkout -b [branch-name]
    ```

3. **Make Changes**: Make your changes and commit them. Follow a clear and concise commit message convention to document your changes.

    ```bash
    git add .
    git commit -m "[Your Commit Message]"
    ```

4. **Push Changes**: Push your changes to your forked repository on GitHub.

    ```bash
    git push origin [branch-name]
    ```

5. **Create a Pull Request**: Once the changes are pushed, create a pull request from your forked repository to the original repository.

6. **Review and Merge**: After a review, your changes may be merged into the original repository.

## Best Practices

- Keep your commits clean and concise.
- Write meaningful commit messages.
- Follow the code style and guidelines of the project.
- Update the README or documentation as needed.
- Write or update tests, if applicable.

## Conclusion

We appreciate any contributions, big or small. Every contribution counts!

Thank you for spending your time to improve Docsible.