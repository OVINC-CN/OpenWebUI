## 自定义品牌配置

> [!WARNING]  
> 本项目是开源分发版本，与 Open WebUI 官方无直接关联  
> 我们鼓励大家支持开源项目，保留 Open WebUI 的标识  
> 如您通过下述方式移除 Open WebUI 标识，请确保满足 [Open WebUI License 条款9](https://docs.openwebui.com/license#9-what-about-forks-can-i-start-one-and-remove-all-open-webui-mentions) 相关条件  
> 未经授权的大规模或商用修改属于违规，由使用者本人承担全部法律风险  
> 以下内容仅供小规模、实验或已授权用户使用

您可以通过设置以下环境变量来自定义系统的名称和 Logo（支持 `.env` 文件或 Docker 环境变量）：

```bash
# 配置为任意非空值即可
LICENSE_KEY: "enterprise"

# 组织名称，填写你喜欢的名称
ORGANIZATION_NAME: "XXX"

# 网站名称
CUSTOM_NAME: "XXX"

# 网站 Logo，ICO 格式
CUSTOM_ICO: "https://example.com/favicon.ico"

# 网站 Logo，PNG 格式
CUSTOM_PNG: "https://example.com/favicon.png"

# 网站深色模式 LOGO，PNG 格式
CUSTOM_DARK_PNG: "https://example.com/favicon.png"

# 网站 Logo，SVG 格式
CUSTOM_SVG: "https://example.com/favicon.svg"
```
