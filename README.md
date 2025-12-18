<div align="center">
  <a href="https://github.com/open-webui/open-webui">
    <img src="./static/favicon.png" alt="Logo" width="100" height="100">
  </a>

  <h1 align="center">Open WebUI (OVINC-CN)</h1>

  <p align="center">
    <strong>基于 Open WebUI 的增强版：集成计费、支付与企业级用户管理</strong>
  </p>

  <p align="center">
    <a href="https://github.com/ovinc-cn/openwebui/releases">
      <img src="https://img.shields.io/github/v/release/ovinc-cn/openwebui?style=flat-square" alt="Release">
    </a>
    <a href="https://github.com/open-webui/open-webui/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License">
    </a>
    <a href="https://github.com/ovinc-cn/openwebui/pkgs/container/openwebui">
      <img src="https://img.shields.io/badge/container-ghcr.io-blue?style=flat-square&logo=github" alt="GHCR">
    </a>
  </p>

  <br />
</div>

> ⚠️ **注意**：此仓库的 `dev` 分支是开发分支，可能包含不稳定功能。生产环境请务必使用 [Release](https://github.com/ovinc-cn/openwebui/releases) 中的正式版本。
> 本项目是 [Open WebUI](https://github.com/open-webui/open-webui) 的定制分支，与官方团队无关联。

## 📖 简介

这是一个社区驱动的 Open WebUI 增强版本，旨在为个人开发者和中小团队提供开箱即用的**运营化解决方案**。我们在原版强大的对话功能基础上，补充了计费、支付、用户验证等商业化闭环所需的关键特性。

## ✨ 核心特性

| 功能模块 | 说明                                         |
| :--- |:-------------------------------------------|
| 💰 **灵活计费** | 支持按 **Token** 或 **请求次数** 计费，实时扣费并在对话中显示详情。 |
| 💳 **支付集成** | 原生支持**易支付**和**支付宝**（当面付/订单码），轻松实现自助充值。     |
| 📊 **数据报表** | 内置全局积分报表与用户消费记录，运营数据一目了然。                  |
| 🔐 **用户管理** | 支持**邮箱验证**注册与**兑换码**系统，有效控制用户准入与权益分发。      |
| ⚙️ **自定义定价** | 支持对特定模型、搜索工具等进行精细化的自定义倍率或额外收费配置。           |

完整特性列表请参阅 [CHANGELOG_EXTRA.md](./CHANGELOG_EXTRA.md)。

## 📸 功能预览

<details>
<summary>点击展开查看更多截图</summary>

### 积分报表与全局设置
| 积分报表 | 全局设置 |
| :---: | :---: |
| ![usage panel](./docs/usage_panel.png) | ![credit config](./docs/credit_config.png) |

### 用户充值与计费详情
| 用户充值 | 计费详情 |
| :---: | :---: |
| ![user credit](./docs/user_credit.png) | ![usage](./docs/usage.png) |

### 兑换码与注册验证
| 兑换码 | 邮箱验证 |
| :---: | :---: |
| ![redemption code](./docs/redemption.png) | ![email](./docs/sign_verify_user.png) |

</details>

## 🚀 快速部署

部署本版本非常简单，只需替换官方镜像即可。

```bash
# 拉取最新镜像（请将 <版本号> 替换为具体版本，如 v0.3.0）
docker pull ghcr.io/ovinc-cn/openwebui:<版本号>

# 启动容器 (示例)
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/ovinc-cn/openwebui:<版本号>
```

查看最新版本：[Releases](https://github.com/ovinc-cn/openwebui/releases/latest)

## ⚙️ 进阶配置

### 1. 支付宝支付配置

推荐使用 [“订单码支付”](https://open.alipay.com/api/detail?code=I1080300001000068149&index=0)。

1.  **回调地址配置**：
    在支付宝后台配置网关地址和授权回调地址为：
    `https://your-domain.com/api/v1/credit/callback/alipay`
    *(将 `your-domain.com` 替换为你的实际域名)*

2.  **私钥格式转换**：
    支付宝工具生成的私钥需转换为 **PKCS1** 格式。

### 2. 自定义价格配置

支持对请求 Body 内容进行正则匹配计费（如对 Web Search 额外收费）。

```json
[
  {
    "name": "web_search",       // 计费项名称
    "path": "$.tools[*].type",  // JSONPath 路径
    "exists": false,            // 是否仅检测存在性
    "value": "web_search_preview", // 匹配值
    "cost": 1000000             // 价格 (1M 次请求)
  }
]
```

### 3. 注册邮箱验证

开启邮箱验证需配置 SMTP 环境变量：

```env
SMTP_HOST=smtp.email.qq.com
SMTP_PORT=465
SMTP_USERNAME=example@qq.com
SMTP_PASSWORD=your_password
```

### 4. 性能调优

如果遇到 `Chunk too big` 错误，可调整 HTTP Client Read Buffer：

```env
# 默认 64KB，可根据需要增加
AIOHTTP_CLIENT_READ_BUFFER_SIZE=65536
```

## ⚖️ 品牌与版权

*   **官方文档**: [Open WebUI Documentation](https://docs.openwebui.com/)
*   **品牌定制**: 如需自定义 LOGO 或名称，请参考 [docs/BRANDING.md](./docs/BRANDING.md)。请务必遵守 [Open WebUI License](https://docs.openwebui.com/license) 关于品牌保护的规定。
