# OpenClaw Azure One-Click Deployment

[中文](#zh-cn) | [English](#en)

Use the button below to easily deploy OpenClaw to your Azure environment.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fhanhsia%2Fopenclaw-azure-deploy%2Fmain%2Fazuredeploy.json)

<a id="zh-cn"></a>
# 中文部署指南

本指南将引导您完成 OpenClaw 在 Azure 上的完整部署流程。部署完成后，您将自动获得一台配置好的 Ubuntu 虚拟机、持久化数据盘、自动分配的公网域名以及安全的 HTTPS 访问。

## 1. 准备部署信息

在开始部署之前，您需要准备以下信息：

- **Azure OpenAI 终结点** (Endpoint)：例如 `https://your-resource.cognitiveservices.azure.com/`
- **模型部署名称** (Deployment Name)：您在 Azure OpenAI 中部署的模型名称，例如 `gpt-4o`
- **API 密钥** (API Key)：您的 Azure OpenAI 访问密钥
- **SSH 公钥** (SSH Public Key)：用于稍后安全登录虚拟机

如果你还没有 SSH 密钥对，可以参考下方操作系统的具体说明进行生成。

## 2. 一键部署流程

1. 点击上方的 **Deploy to Azure** 按钮。
2. 登录您的 Azure 账号。
3. 在部署页面中，选择或创建一个 **资源组 (Resource Group)**。
4. 填写表单中的必要参数：
   - `vmName`：自定义您的虚拟机名称，例如 `openclaw-prod-001`
   - `adminUsername`：SSH 登录用户名，推荐使用 `azureuser`
   - `sshPublicKey`：粘贴您的 SSH **公钥** `.pub` 文件内容（非私钥）
   - `vmSize`：虚拟机规格，保持默认的 `Standard_B2as_v2` 即可
   - `azureOpenAiEndpoint`：您的 Azure OpenAI 终结点
   - `azureOpenAiDeployment`：您的模型部署名称
   - `azureOpenAiApiKey`：您的 Azure OpenAI API 密钥
5. 点击**查看 + 创建**，然后点击**创建**提交部署。
6. 等待部署完成。请耐心等待，直到所有资源（特别是扩展 `openclaw-bootstrap`）显示部署成功。
7. 部署完成后，点击左侧的**输出 (Outputs)**，记录以下重要信息：
   - `vmPublicFqdn` (虚拟机公网域名，用于稍后 SSH 登录)

## 3. 连接与初始化配置

根据您的操作系统，按照以下步骤登录虚拟机并获取访问令牌。

### Windows 用户操作步骤

#### 准备 SSH 密钥
如果您还没有 SSH 密钥，可以先在 PowerShell 中执行以下命令生成一对新的 SSH 密钥：
```powershell
ssh-keygen -t ed25519 -C "openclaw-azure"
```

生成完成后，再运行以下命令获取公钥内容，并将其粘贴到 Azure 部署表单中：
```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

#### SSH 登录虚拟机
使用您的 SSH 私钥（例如 `id_ed25519`）连接虚拟机：
```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" azureuser@<vmPublicFqdn>
```
*(请将 `<vmPublicFqdn>` 替换为您在部署输出中记录的域名，如有其他私钥名称或位置请相应调整)*

#### 获取 Web 控制台地址
登录成功后在终端执行：
```bash
openclaw-browser-url
```
输出示例：
```text
Dashboard URL: https://your-hostname/#token=...
```
将完整的 URL 复制并在浏览器中打开。

#### 设备配对授权
如果浏览器页面提示 `pairing required` 或需要配对，请保持页面打开，回到 SSH 终端执行以下许可命令：
```bash
openclaw-approve-browser
```
命令执行完毕后，回到浏览器刷新页面即可完成登录。

---

### macOS / Linux 用户操作步骤

#### 准备 SSH 密钥
查看现有的公钥并复制整行内容到 Azure 表单：
```bash
cat ~/.ssh/id_ed25519.pub
```
如果没有密钥，请先运行以下命令生成：
```bash
ssh-keygen -t ed25519 -C "openclaw-azure"
cat ~/.ssh/id_ed25519.pub
```

#### SSH 登录虚拟机
```bash
ssh -i ~/.ssh/id_ed25519 azureuser@<vmPublicFqdn>
```
*(请将 `<vmPublicFqdn>` 替换为您在部署输出中记录的域名)*

#### 获取 Web 控制台地址
登录成功后在终端执行：
```bash
openclaw-browser-url
```
将终端输出的完整 Dashboard URL 复制并在浏览器中打开。

#### 设备配对授权
如果浏览器页面提示需要配对授权，请回到 SSH 终端执行：
```bash
openclaw-approve-browser
```
然后返回浏览器刷新页面，即可正常使用 OpenClaw。

## 进阶：使用 Azure CLI 部署（替代方案）

如果您熟悉命令行操作，也可以跳过网页一键部署，直接使用 Azure CLI 完成部署。此方式适合自动化脚本或不方便使用浏览器的场景。

### 1. 登录 Azure 账号
```bash
az login
```

### 2. 创建资源组
在开始部署前，先指定一个位置（例如 `southeastasia`）来创建您的资源组：
```bash
az group create --name rg-openclaw-sea --location southeastasia
```

### 3. 执行部署命令
在此命令中直接填入您的自定义参数。部署过程可能需要几分钟。
```bash
az deployment group create \
  --name openclaw-sea-20260307 \
  --resource-group rg-openclaw-sea \
  --template-uri https://raw.githubusercontent.com/hanhsia/openclaw-azure-deploy/main/azuredeploy.json \
  --parameters \
    vmName=openclaw-sea-20260307 \
    adminUsername=azureuser \
    sshPublicKey="ssh-ed25519 AAAA..." \
    vmSize=Standard_B2as_v2 \
    azureOpenAiEndpoint="https://your-resource.cognitiveservices.azure.com/" \
    azureOpenAiDeployment="gpt-5.2" \
    azureOpenAiApiKey="replace-with-api-key"
```

### 4. 查看部署输出
部署成功后，控制台会输出大量的 JSON 信息，您可以在输出结果底部找到 `outputs` 节点，里面包含虚拟机的公网域名（`vmPublicFqdn`）。
如果您不小心清空了终端，可以随时通过以下命令再次查看部署输出：
```bash
az deployment group show \
  --name openclaw-sea-20260307 \
  --resource-group rg-openclaw-sea \
  --query properties.outputs
```
拿到公网域名后，后续的步骤与上述的【3. 连接与初始化配置】完全相同。

## 常见问题

### 1. SSH 报错 `Permission denied (publickey)`
**原因：** 您使用的私钥与提供给 Azure 的公钥不匹配，或者您没有使用 `-i` 参数指定正确的私钥路径。  
**解决办法：** 
- 确保部署时粘贴的公钥内容（`.pub`）与您当前使用的私钥是一对。
- 如果您在 Azure 门户下载了 `.pem` 文件，登录时请通过 `-i` 参数明确指定：
  ```bash
  ssh -i <你的私钥文件路径.pem> azureuser@<vmPublicFqdn>
  ```

### 2. SSH 报错 `UNPROTECTED PRIVATE KEY FILE` 或者 `Permissions 0644 for ... are too open`
**原因：** 您的私钥文件权限过于宽松，SSH 客户端出于安全考虑拒绝使用它。  
**解决办法：**  
- **Windows 用户：** 在 PowerShell 中执行以下命令（假设您的私钥名为 `openclaw-key.pem`）：
  ```powershell
  $Key = "$env:USERPROFILE\.ssh\openclaw-key.pem"
  icacls $Key /inheritance:r
  icacls $Key /remove:g "Users" "Authenticated Users" "Everyone" "BUILTIN\Administrators"
  icacls $Key /grant:r "${env:USERNAME}:R"
  ```
- **Mac / Linux 用户：** 在终端中执行以下命令限制权限：
  ```bash
  chmod 600 ~/.ssh/openclaw-key.pem
  ```

### 3. 如何找到 `gateway token`（网关令牌）缺少的提示？
**原因：** OpenClaw 面板采用了基于 Token 的安全验证，不允许直接通过裸域名访问，直接输入 URL 时会被拒绝。  
**解决办法：**  
切勿手动猜测或输入 Token。请 SSH 登录进虚拟机，直接运行：
```bash
openclaw-browser-url
```
它会直接输出完整的 `https://.../#token=...` 链接，复制整段带有 token 的 URL 在浏览器中打开即可。

### 4. 浏览器显示 `pairing required`（需要设备配对）
**原因：** 为了安全限制，您的浏览器设备作为一个新的客户端首次连接网关时，需要进行管理员授权。  
**解决办法：**  
保持该浏览器页面不要关闭，此时切回虚拟机的 SSH 终端，执行以下命令进行授权：
```bash
openclaw-approve-browser
```
命令执行完毕后，回到浏览器刷新页面即可直接进入面板。

### 5. 浏览器访问报错 `502 Bad Gateway`
**原因：** 部署尚未完全结束，或者内部的 Docker 容器服务（Gateway 或 Caddy）未成功启动或正在重启中。  
**解决办法：**  
1. 刚刚部署完毕时，请等待 1-2 分钟让组件完全启动。
2. 如果持续报错，请登录至虚拟机排查容器状态：
   ```bash
   # 查看哪些容器不在 running 状态
   sudo docker ps -a
   
   # 如果 gateway 服务一直重启，可以查看具体错误日志（如 API Key 是否填错导致连接大模型失败）
   sudo docker logs --tail 100 openclaw-gateway
   
   # 查看反向代理层的日志
   sudo docker logs --tail 100 openclaw-caddy
   ```

### 6. 无法连接虚拟机（Connection Timed Out）
**原因：** 虚拟机实例没有成功获取公网 IP，或者其 22 / 443 端口被安全组（NSG）阻挡。  
**解决办法：**  
- 在 Azure 门户中前往您刚刚部署的**虚拟机**页面。
- 检查处于 `Running(正在运行)` 状态，并且确认分配到了 Public IP。
- 点击左侧的**网络 (Networking)**，确保入站端口规则 (Inbound port rules) 允许了 `22` (SSH) 和 `443` (HTTPS) 端口。

---

<a id="en"></a>
# English

## What this repository is

This is a minimal end-user repository for one-click OpenClaw deployment on Azure.

After deployment you get:

- One Ubuntu VM
- A persistent data disk mounted at `/data`
- An Azure-generated public `*.cloudapp.azure.com` hostname
- Automatic HTTPS via Caddy
- OpenClaw connected to Azure OpenAI
- Two helper commands: `openclaw-browser-url` and `openclaw-approve-browser`

## What users need before deployment

Prepare these values:

- `vmName`: VM name, for example `openclaw-sea-20260307`
- `adminUsername`: SSH login username, for example `azureuser`
- `sshPublicKey`: SSH public key content
- `vmSize`: VM SKU, default `Standard_B2as_v2`
- `azureOpenAiEndpoint`: for example `https://your-resource.cognitiveservices.azure.com/`
- `azureOpenAiDeployment`: for example `gpt-5.2`
- `azureOpenAiApiKey`: Azure OpenAI API key

Users do not need to provide these values:

- `location`: automatically uses the resource group region
- `Key pair name`: not required by OpenClaw
- `OpenClaw Image`: fixed internally by the template
- `Gateway Token`: generated automatically during deployment

## One-click deployment steps

1. Click the `Deploy to Azure` button above.
2. Sign in to Azure.
3. Select or create a resource group.
4. Fill in the required parameters.
5. Start deployment.
6. Wait for the VM extension `openclaw-bootstrap` to finish successfully.
7. Record the outputs:
   - `vmPublicFqdn` (VM public domain name, used later for SSH login)

## How to fill the form

Recommended values:

- `vmName`: for example `openclaw-prod-001`
- `adminUsername`: recommended `azureuser`
- `sshPublicKey`: paste the full content of your `.pub` file
- `vmSize`: keep the default unless you need a different size
- `azureOpenAiEndpoint`: your Azure OpenAI endpoint
- `azureOpenAiDeployment`: your Azure model deployment name
- `azureOpenAiApiKey`: your Azure OpenAI API key

## Complete Windows steps

### 1. Prepare your SSH key

If you do not have an SSH key yet, first generate a new key pair in PowerShell:

```powershell
ssh-keygen -t ed25519 -C "openclaw-azure"
```

Then print the public key:

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

Paste the full line into the Azure form field `sshPublicKey`.

If Azure generated and downloaded a file such as `openclaw-key.pem`, that file is your private key for SSH login later. It is not the value to paste into the deployment form.

### 2. Fix `.pem` file permissions after deployment

Run this in PowerShell:

```powershell
$KeySrc = "$env:USERPROFILE\Downloads\openclaw-key.pem"
$KeyDst = "$env:USERPROFILE\.ssh\openclaw-key.pem"

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
Copy-Item -Force $KeySrc $KeyDst

icacls $KeyDst /inheritance:r
icacls $KeyDst /remove:g "Users" "Authenticated Users" "Everyone" "BUILTIN\Administrators"
icacls $KeyDst /grant:r "${env:USERNAME}:R"
```

### 3. SSH into the VM

If you use the Azure-downloaded `.pem`:

```powershell
ssh -i "$env:USERPROFILE\.ssh\openclaw-key.pem" azureuser@<vmPublicFqdn>
```

If you use your own existing private key:

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" azureuser@<vmPublicFqdn>
```

### 4. Get the dashboard URL

After login, run:

```bash
openclaw-browser-url
```

It prints a complete dashboard URL like:

```text
Dashboard URL: https://your-hostname/#token=...
```

Open that full URL in your browser.

### 5. If the UI says pairing is required

Run on the VM:

```bash
openclaw-approve-browser
```

Then refresh the browser.

### 6. If you need the raw token only

```bash
sudo grep '^OPENCLAW_GATEWAY_TOKEN=' /etc/openclaw/openclaw.env
```

## Complete macOS / Linux steps

### 1. Prepare your SSH key

If you already have one:

```bash
cat ~/.ssh/id_ed25519.pub
```

Paste the full line into `sshPublicKey`.

If you do not have a key yet, generate one and then print the public key:

```bash
ssh-keygen -t ed25519 -C "openclaw-azure"
cat ~/.ssh/id_ed25519.pub
```

### 2. SSH into the VM

If you use your own private key:

```bash
ssh -i ~/.ssh/id_ed25519 azureuser@<vmPublicFqdn>
```

If you use an Azure-generated `openclaw-key.pem` file:

```bash
chmod 600 ~/Downloads/openclaw-key.pem
ssh -i ~/Downloads/openclaw-key.pem azureuser@<vmPublicFqdn>
```

### 3. Get the dashboard URL

Run:

```bash
openclaw-browser-url
```

Copy the full printed URL into your browser.

### 4. If the UI says pairing is required

```bash
openclaw-approve-browser
```

Then refresh the browser.

### 5. If you need the raw token only

```bash
sudo grep '^OPENCLAW_GATEWAY_TOKEN=' /etc/openclaw/openclaw.env
```

## Advanced: Azure CLI Deployment (Alternative)

If you are comfortable with the command line, you can skip the web-based one-click deployment and use the Azure CLI instead. This is particularly useful for automation scripts or when a browser is unavailable.

### 1. Log in to Azure
```bash
az login
```

### 2. Create a Resource Group
Before deploying, create a resource group in your preferred location (e.g., `southeastasia`):
```bash
az group create --name rg-openclaw-sea --location southeastasia
```

### 3. Run the Deployment
Provide your custom parameters in the command below. The deployment may take a few minutes.
```bash
az deployment group create \
  --name openclaw-sea-20260307 \
  --resource-group rg-openclaw-sea \
  --template-uri https://raw.githubusercontent.com/hanhsia/openclaw-azure-deploy/main/azuredeploy.json \
  --parameters \
    vmName=openclaw-sea-20260307 \
    adminUsername=azureuser \
    sshPublicKey="ssh-ed25519 AAAA..." \
    vmSize=Standard_B2as_v2 \
    azureOpenAiEndpoint="https://your-resource.cognitiveservices.azure.com/" \
    azureOpenAiDeployment="gpt-5.2" \
    azureOpenAiApiKey="replace-with-api-key"
```

### 4. View Deployment Outputs
Once successful, the console will output a large JSON object. Look for the `outputs` section at the bottom, which contains the VM's public domain name (`vmPublicFqdn`).
If you miss the output, you can retrieve it anytime by running:
```bash
az deployment group show \
  --name openclaw-sea-20260307 \
  --resource-group rg-openclaw-sea \
  --query properties.outputs
```
After obtaining the public domain name, all subsequent steps are identical to the "Connection and Initial Setup" / SSH login steps detailed above.

## Troubleshooting

### 1. SSH returns `Permission denied (publickey)`
**Cause:** The private key you are using does not match the public key stored on the VM, or you didn't specify the correct path to your private key.  
**Solution:**
- Verify that the `sshPublicKey` content provided during deployment pairs with the private key on your local machine.
- If you downloaded a `.pem` key from the Azure Portal, explicitly pass it using the `-i` flag:
  ```bash
  ssh -i </path/to/your-key.pem> azureuser@<vmPublicFqdn>
  ```

### 2. SSH returns `UNPROTECTED PRIVATE KEY FILE` or `Permissions 0644 for ... are too open`
**Cause:** Security mechanisms prevent SSH clients from using private key files with overly broad permissions (e.g., readable by other users).  
**Solution:**  
- **For Windows:** Run these commands in PowerShell (assuming your key is `openclaw-key.pem`):
  ```powershell
  $Key = "$env:USERPROFILE\.ssh\openclaw-key.pem"
  icacls $Key /inheritance:r
  icacls $Key /remove:g "Users" "Authenticated Users" "Everyone" "BUILTIN\Administrators"
  icacls $Key /grant:r "${env:USERNAME}:R"
  ```
- **For macOS/Linux:** Restrict permissions directly in the terminal:
  ```bash
  chmod 600 ~/.ssh/openclaw-key.pem
  ```

### 3. Missing `gateway token` or denied access to the web dashboard
**Cause:** OpenClaw secures its console via a hashed token in the URL anchor. Attempting to navigate strictly to the bare domain will block you.  
**Solution:**  
Never attempt to guess the token or bypass it. From your VM's SSH terminal, execute:
```bash
openclaw-browser-url
```
Copy and paste the entire output starting with `https://` (which includes `#token=...`) into your browser.

### 4. UI says `pairing required`
**Cause:** To prevent unauthorized entities from connecting to your OpenClaw node, new browser clients must be approved by an administrator connection (SSH).  
**Solution:**  
Keep the “pairing required” browser tab open. Return to your SSH terminal on the VM and execute:
```bash
openclaw-approve-browser
```
Once it succeeds, switch back to the browser and refresh the page.

### 5. Browser shows `502 Bad Gateway`
**Cause:** The virtual machine has booted, but the underlying Docker containers (Gateway or Caddy proxy) have not finished initializing, or encountered an error (e.g., invalid Azure OpenAI credentials causing crash loop).  
**Solution:**  
1. Wait 1-2 minutes and refresh the page. 
2. If it persists, SSH into the VM and diagnose the container states:
   ```bash
   # Check container status
   sudo docker ps -a
   
   # Inspect gateway crashes (e.g., failed to connect to LLM)
   sudo docker logs --tail 100 openclaw-gateway
   
   # Inspect proxy logs
   sudo docker logs --tail 100 openclaw-caddy
   ```

### 6. SSH or Browser Connection Timed Out
**Cause:** The public IP hasn't been properly assigned by Azure, or network traffic is blocked by a Network Security Group (NSG).  
**Solution:**  
- Open your target VM in the Azure Portal.
- Ensure the state shows `Running` and it has a valid `Public IP address`.
- Go to the **Networking** blade in the left menu, and ensure the *Inbound port rules* allow traffic on ports `22` (SSH) and `443` (HTTPS) from your current IP.
