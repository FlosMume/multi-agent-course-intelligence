# Environment Plan

## Target location

```text
/home/myunix/edu/multi-agent-course-intelligence/
```

Keep the repository in the WSL Linux filesystem rather than under `/mnt/c`.
The working path must begin with
`/home/myunix/edu/multi-agent-course-intelligence/`.

## Environment isolation

Create a dedicated Conda environment so this framework comparison can pin and
change dependencies without affecting the earlier native-agent project.

```bash
cd /home/myunix/edu
conda create -n course-intelligence-lab python=3.12 -y
conda activate course-intelligence-lab
```

Python 3.11+ is supported; Python 3.12 is the reference environment.

## Read-only preflight

After the project folder has been created and the Phase 0 files have been
extracted into it, run these commands before installing dependencies:

```bash
cd /home/myunix/edu/multi-agent-course-intelligence/
pwd
which python
python --version
git --version
conda info --envs
ollama --version
curl http://localhost:11434/api/tags
```

Expected conditions:

- the working path begins with
  `/home/myunix/edu/multi-agent-course-intelligence/`;
- Python resolves inside `course-intelligence-lab`;
- Python is 3.11 or newer;
- Git and Ollama respond;
- Ollama lists at least one local model.

## Installation sequence

Use `git init` to initialize the working path before dependency installation or
validation:

```bash
cd /home/myunix/edu/multi-agent-course-intelligence/
git init
git branch -M main
git status

python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
python -m ruff check .
python -m pytest

git add .
git status
```

Review `git status` before the first commit. Do not commit `.env`.

## Local inference

The default configuration uses Ollama's OpenAI-compatible base URL:

```text
http://localhost:11434/v1
```

The initial reference model is `qwen2:7b-instruct`, subject to a capability
check before Phase 1. Tool calling and structured-output behaviour must be
tested rather than assumed from the model name.

## Optional cloud inference

Cloud inference remains disabled until `CLOUD_MODEL_ENABLED=true`. Credentials
belong only in the local `.env` or an operating-system secret store. Each cloud
run must record provider, model, parameters, and estimated cost while excluding
the credential itself.

## Dependency strategy

- Phase 0 installs only Pydantic, settings support, Pytest, and Ruff.
- Each framework phase adds a named optional dependency group.
- Framework versions are pinned at the start of their phase.
- A lock or explicit environment export is produced after the comparison stack
  is stable.
- Unit tests remain network-free regardless of installed frameworks.

## Git practice

Use one reviewed commit per meaningful milestone. Suggested Phase 0 commit:

```text
chore: establish framework-neutral Phase 0 foundation
```

Do not publish a remote repository until documentation, license choice, and
example-data licensing have been reviewed.
