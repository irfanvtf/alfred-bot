# Contributing to Alfred Bot

First off, thank you for considering contributing to Alfred Bot! It's people like you that make open source great.

## How to Get Started

- **Fork the repository** on GitHub.
- **Clone your fork** to your local machine.
- **Set up the development environment** by following the instructions in the [usage.md](./docs/usage.md) guide.

## Reporting Bugs

If you find a bug, please open an issue on GitHub and provide the following information:

- A clear and descriptive title.
- A detailed description of the problem, including steps to reproduce it.
- The expected behavior and what actually happened.
- Your environment details (e.g., operating system, Python version).

## Suggesting Enhancements

If you have an idea for a new feature or an improvement, please open an issue on GitHub. Describe your idea and why you think it would be a good addition to the project.

## Your First Code Contribution

Unsure where to begin? You can start by looking through the open issues for bugs or feature requests.

## Pull Request Process

1. **Create an Issue**: Start by creating a GitHub issue for bugs or feature requests.

2. **Create Jira Ticket**: Create a corresponding Jira ticket with detailed description and update the GitHub issue title to include the Jira ticket number.

3. **Branch Development**:

   - Create a separate branch for your changes
   - Use descriptive branch names with ticket numbers when possible:
     - `feature/[Jira-ticket]-add-session-timeout`
     - `bug/[Jira-ticket]-fix-redis-connection`
     - `docs/[Jira-ticket]-update-api-documentation`
   - Make your changes and push to the branch

4. **Submit Pull Request**:

   - Use a clear, simple title
   - Include detailed description of changes and action items
   - Link the PR to the related GitHub issue(s)
   - Ensure all tests pass and code follows formatting standards (black, flake8)

5. **Code Review**:

   - Wait for CodeRabbit automated review
   - Address any feedback or issues raised
   - Once approved, the PR can be merged

6. **Deployment Process**:
   - Changes are first deployed to staging for testing and stability
   - After testing, changes are pushed to main branch
   - Version numbers and changelog are updated only when pushing to main
   - Follow [SemVer](http://semver.org/) versioning scheme

## Branch Strategy

- `main`: Production-ready code
- `staging`: Testing and stability branch
- `feature/*`: New features and enhancements
- `bug/*`: Bug fixes and patches
- `docs/*`: Documentation updates
- Always create PRs from these branches to staging first, then staging to main

## Coding Standards

- **Code Formatting:** Please format your code using `black`.
- **Linting:** Please ensure your code passes `flake8` checks.
- **Tests:** Please add tests for any new features or bug fixes.
