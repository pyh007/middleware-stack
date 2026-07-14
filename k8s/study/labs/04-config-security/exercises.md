# 配置与安全练习题

1. ConfigMap 和 Secret 的边界是什么，为什么 Secret 默认不代表安全存储已经完成？
2. 修改 ConfigMap 后，环境变量注入和卷挂载的应用行为有何不同？
3. ServiceAccount、Role、RoleBinding 各自解决什么问题？
4. `kubectl auth can-i` 返回 no 时，应该核对哪些身份和资源字段？
5. `runAsNonRoot`、`allowPrivilegeEscalation: false`、drop capabilities 和 seccomp 分别减少什么风险？
6. 为什么生产应用不应共享一个高权限 ServiceAccount？
