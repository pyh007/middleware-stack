# Quality gates

Do not call a middleware curriculum complete until every applicable gate passes.

## Content gates

- Provide navigation, roadmap, quick reentry, labs, cases, interview questions, review instructions, and runbooks.
- Replace all `TODO`, `FIXME`, `TBD`, placeholder text, and “待建设” statuses.
- Give every module goals, mechanisms, commands, observations, production boundaries, and completion criteria.
- Make answers explain mechanisms and tradeoffs; reject absolute slogans without scope.
- End with an integrated production incident or capstone.

## Experiment gates

- Use deterministic seed data or a documented controlled generator.
- Make the normal lab repeatable without manual cleanup.
- State expected observable evidence: plans, metrics, offsets, locks, lag, recovered rows, memory, or logs.
- Assert important invariants where scripts can do so reliably.
- Isolate modules so running the full suite yields the same result as running each module alone.
- Prefer native clients and protocols over ORMs or frameworks when teaching internals.

## Safety gates

- Bind local services to loopback unless cross-host access is intentional.
- Mark credentials as local-only and never reuse them as production guidance.
- Scope reset operations to lab prefixes, isolated databases, topics, indices, or consumer groups.
- Exclude crashes, volume deletion, failover, large load, and extra clusters from the safe aggregate command.
- Explain affected containers, ports, data, cleanup, and recovery before destructive commands.
- Preserve existing user data and dirty worktree changes.

## Production gates

- Include monitoring signals, diagnosis order, mitigation, validation, and rollback.
- Connect performance changes to write cost, capacity, concurrency, and topology effects.
- Include backup restore or state recovery where the middleware persists data.
- Include security, credential lifecycle, least privilege, network exposure, and audit concerns.
- Define RPO/RTO or the equivalent loss and recovery expectations where applicable.

## Retention gates

- Maintain L0-L4 mastery and review dates.
- Provide a 15-minute reentry path.
- Link every question-bank entry to an existing lab, case, or runbook.
- Use approximately day 1, 3, 7, 14, 30, and 90 review intervals.

## Verification gates

- Run the official Skill validator.
- Run the curriculum validator.
- Execute the safe aggregate command.
- Execute special labs separately, then clean additional resources.
- Recheck service health, stale paths, broken links, script syntax, and repository diff.
- Report measured evidence and any genuinely unfinished work.

## Common failure patterns

- Creating a polished roadmap while leaving later modules empty.
- Copying one middleware's topic names into another domain.
- Treating a single demo as production readiness.
- Adding many notes without executable evidence.
- Making reset delete non-lab data.
- Using screenshots instead of reproducible output.
- Claiming success because a command exited zero without validating business state.
- Leaving a multi-node lab running after validation without telling the user.
