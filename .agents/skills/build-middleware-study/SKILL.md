---
name: build-middleware-study
description: Build, extend, reorganize, or audit a reusable middleware learning system with runnable labs, active-recall questions, interview preparation, production runbooks, incident cases, spaced review, and quality validation. Use when Codex needs to create or improve a `study/` curriculum for MySQL, Redis, Kafka, Elasticsearch, RabbitMQ, or similar infrastructure middleware, especially when the goal includes both interviews and production use rather than a collection of demos or notes.
---

# Build Middleware Study

Create a durable learning system that proves knowledge through repeatable experiments and supports fast relearning after forgetting.

## Follow the workflow

1. Inspect the repository, `AGENTS.md`, existing runtime, commands, dirty changes, and current learning artifacts. Preserve unrelated work.
2. Read [references/architecture.md](references/architecture.md) and [references/quality-gates.md](references/quality-gates.md).
3. Read [references/domain-planning.md](references/domain-planning.md) only for the middleware being planned or when the topic map is unclear.
4. Decide whether to initialize, extend, reorganize, or audit. Do not overwrite a functioning runtime or existing study content.
5. Build a middleware-specific curriculum from the common learning dimensions. Default to eight modules, but use six to ten when the domain justifies it. Do not mechanically copy MySQL topics into another middleware.
6. Put runtime infrastructure and the command entrypoint at the middleware root. Put all course content under `<middleware>/study/`.
7. Implement complete modules, runnable experiments, review questions, incident cases, and runbooks. Keep destructive or resource-heavy experiments explicit and outside the default safe suite.
8. Run the experiments in the actual local environment. Fix failures and cross-module contamination. Never mark a placeholder or unexecuted lab complete.
9. Run `scripts/validate_study.py` and resolve every error before reporting completion.

## Initialize a new curriculum

Use the initializer only for a new or intentionally merged curriculum:

```bash
python scripts/init_study.py \
  --middleware Redis \
  --target /path/to/repository/redis \
  --modules 'data-structures:数据结构与建模,expiration-eviction:过期与淘汰,performance:性能与热点诊断,concurrency:并发与一致性,persistence:持久化,replication-cluster:复制与集群,production-ops:生产运维与恢复,incident-interview:综合事故与面试'
```

The generated files deliberately contain `TODO` markers. Replace them with domain-specific content and real labs; the validator must reject untouched scaffolding.

Use `--merge` only to add missing files. Never use it as permission to replace user-authored content.

## Design the curriculum

Cover these dimensions across the course:

1. Mental model and data path.
2. Correct usage and business design.
3. Performance and observability.
4. Concurrency, ordering, and consistency.
5. Storage, persistence, and recovery.
6. Replication, clustering, and availability.
7. Production operations, capacity, and security.
8. Integrated incidents and interview expression.

Allow a module to combine dimensions when the middleware naturally couples them. Require every curriculum to end with a production incident or capstone.

## Implement each module

Create:

- `README.md`: goals, mechanism, run command, observations, production boundaries, and completion criteria.
- `exercises.md`: questions that require recall before rereading.
- `answers.md`: mechanisms, tradeoffs, and validation evidence rather than memorized slogans.
- One or more runnable labs using the middleware's native CLI, SQL, scripts, or containers.

Make experiments deterministic, repeatable, observable, and safely resettable. Prefer native behavior over framework abstractions. State expected evidence and require the learner to modify at least one variable.

## Integrate commands and safety

Keep a stable command entrypoint such as the middleware-root `Makefile`. Provide at least:

- `help`, `up`, `down`, `reset`, `review`, and a safe aggregate command.
- One discoverable command per module.
- Separate explicit commands for crashes, data deletion, failover, extra clusters, or expensive loads.

Bind local services to loopback where practical. Label credentials as local-only. Preserve non-lab data during reset by using a consistent lab prefix or isolated database.

## Build retention and production transfer

Maintain `ROADMAP.md` with L0–L4 mastery, review dates, and evidence. Maintain `CHEATSHEET.md` as a 15-minute reentry map, not a second textbook. Use spaced review at approximately days 1, 3, 7, 14, 30, and 90.

Link every interview question to a real lab, case, or runbook. Structure answers as:

```text
conclusion → mechanism → evidence → boundary → side effect → production validation
```

## Validate completion

Run:

```bash
python scripts/validate_study.py /path/to/middleware/study
```

Then execute the safe aggregate command plus every destructive or multi-node lab separately. Record concrete evidence such as scanned rows, observed locks, restored records, replica state, or recovered data.

Report what was implemented, what was actually executed, destructive commands that remain opt-in, and any unfinished work. Do not describe a roadmap placeholder as a completed module.
