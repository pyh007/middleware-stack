# 04 配置、身份、RBAC 与安全边界

## 学习目标

区分 ConfigMap 与 Secret 的用途和限制；理解 ServiceAccount 身份、RBAC 授权、令牌挂载以及 Pod/容器 securityContext；能以最小权限而不是集群管理员权限部署应用。

## 核心机制

ConfigMap 保存非敏感配置，Secret 只是专用对象，默认并不等同于加密保险箱。配置可以通过环境变量或卷进入容器：环境变量只在进程启动时读取，卷投影会异步更新。ServiceAccount 提供工作负载身份，Role 定义 Namespace 内允许的动作，RoleBinding 把身份与权限连接。容器安全还需要非 root、禁止提权、丢弃 Linux capabilities、seccomp、只读文件系统和镜像治理等组合措施。

## 实验

```bash
make -C k8s config-security
```

实验把 ConfigMap 和本地 Secret 注入非 root 容器，只输出 Secret 长度而不打印内容；同时创建只能读取 ConfigMap 的 ServiceAccount，使用 `kubectl auth can-i` 断言读取 ConfigMap 为 yes、读取 Secret 为 no。修改 Role 前先预测授权结果。

## 生产边界

本地 Secret 示例不能复制到生产。生产需考虑外部密钥系统、静态加密、密钥轮换、审计、短期令牌、镜像签名、准入策略和 Namespace 边界。`cluster-admin` 能快速绕过问题，但会扩大泄露和误操作半径；授权排障应确认调用身份、verb、resource、subresource 和 Namespace。

## 完成标准

能解释认证、授权和准入的顺序；能写出最小 Role/RoleBinding 并证明拒绝路径；能说明环境变量与卷投影的更新差异；能对一个 Pod securityContext 给出至少三项风险改进及兼容性验证。
