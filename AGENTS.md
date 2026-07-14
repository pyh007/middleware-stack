# 仓库协作约定

- 所有面向用户的回复使用中文。
- 新建、扩展、重构或审计中间件学习体系时，使用 `$build-middleware-study` Skill。
- 中间件运行环境和统一命令入口放在中间件根目录，所有课程内容放在 `<middleware>/study/`。
- 每个学习模块必须包含原理、练习题、答案和真实可运行实验；不得把“待建设”占位描述为已完成。
- 破坏性、故障注入、多节点和高负载实验必须使用显式命令，不得加入默认安全全量任务。
- 完成学习体系变更后，运行 `.agents/skills/build-middleware-study/scripts/validate_study.py`，并实际执行相关实验。
- 仓库级 Skill 位于 `.agents/skills/build-middleware-study/`，供本仓库所有中间件目录自动发现和复用。
