# 配置与安全参考答案

1. ConfigMap 用于非敏感配置，Secret 用于敏感字节和专用引用方式，但对象内容通常只是 base64 表示。还需要 etcd 静态加密、传输加密、最小 RBAC、外部密钥管理、轮换和审计。
2. 环境变量在容器进程启动时固定，修改对象不会刷新现有进程；卷投影通常会在一段时间后更新文件，但使用 subPath 等方式可能不更新，应用也必须重新加载。上线前应实测传播和回滚。
3. ServiceAccount 是工作负载身份，Role 是 Namespace 内的一组授权规则，RoleBinding 把用户、组或 ServiceAccount 绑定到 Role/ClusterRole。身份存在不代表自动获得权限。
4. 核对实际用户名或 ServiceAccount、verb、apiGroup、resource、resourceName、subresource 和 Namespace，并检查多个绑定的合并结果。RBAC 权限是加法，没有显式 deny。
5. 非 root 降低 root 逃逸后影响，禁止提权阻止 setuid 等获得更高权限，drop capabilities 移除内核特权，seccomp 限制系统调用面。它们需要结合镜像运行用户和写目录做兼容验证。
6. 独立身份便于最小权限、审计、轮换和快速吊销。共享高权限身份会扩大泄露半径，让日志无法区分调用方，并使某个应用漏洞影响整个 Namespace 或集群。
