# Middleware study architecture

## Repository contract

Keep runtime concerns separate from learning content:

```text
<middleware>/
├── docker-compose.yml        local runtime, if applicable
├── Makefile                  stable command entrypoint
└── study/
    ├── README.md             navigation and learning map
    ├── ROADMAP.md            L0-L4 progress and review dates
    ├── CHEATSHEET.md         15-minute reentry map
    ├── labs/                 ordered course modules
    ├── cases/                integrated incidents
    ├── interview/            structured question bank
    ├── review/               active-recall instructions
    ├── runbooks/             production diagnosis and recovery
    └── scripts/              seed, reset, review, and validation helpers
```

Keep all learner-facing artifacts inside `study/`. Keep runtime orchestration outside it so production-like topology and learning material can evolve independently.

## Module contract

Use ordered directories such as `01-data-model` or `04-consistency`. Each module must contain:

```text
README.md
exercises.md
answers.md
one or more runnable lab artifacts
```

Allow `.sql`, `.py`, `.sh`, native configuration, and module-local Compose files. Choose the lowest abstraction that exposes the middleware behavior.

## Learning loop

Build every module around:

```text
concept → minimal lab → failure injection → evidence → fix → interview expression → production boundary
```

Require the learner to predict the result before execution and modify one variable afterward. Store reproducible commands and expected evidence, not screenshots tied to one run.

## Mastery and retention

Use:

- L0: cannot explain reliably.
- L1: can explain in original words.
- L2: can reproduce and explain the experiment.
- L3: can diagnose from metrics, logs, or plans.
- L4: can choose a design and defend tradeoffs.

Track the last review, next review, and evidence. Use active recall before rereading. Provide a quick path that restores the topic map, samples questions, reruns one lab, and records the weakest point within 15 minutes.

## Command contract

Expose predictable commands without forcing every middleware to use identical implementation details:

- `help`: enumerate commands and risk.
- `up` / `down`: manage the default local runtime.
- `reset`: remove lab-scoped data only.
- `review`: sample questions before showing answers.
- safe aggregate: run deterministic non-destructive labs.
- explicit dangerous targets: crashes, failovers, destructive recovery, heavy loads, and extra clusters.

Do not include dangerous targets as dependencies of the safe aggregate command.

## Evolution contract

Treat the Skill as the reusable method and the repository as the evidence-bearing instance. Improve the Skill when the same failure appears in more than one middleware. Keep domain-specific commands and conclusions in the repository unless they generalize.
