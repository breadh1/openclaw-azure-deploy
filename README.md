# OpenClaw Azure 一鍵部署

[中文](#zh-cn) | [English](#en)

Azure 全球使用者 / Azure Global users:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fbreadh1%2Fopenclaw-azure-deploy%2Fmain%2Fazuredeploy.json/createUIDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2Fhanhsia%2Fopenclaw-azure-deploy%2Fmain%2FcreateUiDefinition.json)

---

<a id="zh-cn"></a>
# 中文部署指南

## 1. 準備 SSH 金鑰

如果您已有 SSH 金鑰對，可以跳過此步驟。

**Windows（PowerShell）：**
```powershell
ssh-keygen -t ed25519 -C "openclaw-azure"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

**macOS / Linux：**
```bash
ssh-keygen -t ed25519 -C "openclaw-azure"
cat ~/.ssh/id_ed25519.pub
```

複製輸出的公鑰內容，稍後貼到部署表單中。

## 2.（選填）準備 Azure OpenAI 資訊

如果您希望部署後立即使用 Azure OpenAI，請根據認證方式準備以下資訊：

| 參數 | API Key 模式 | Managed Identity 模式（建議） |
|------|------------|--------------------------|
| Azure OpenAI 端點 | 必填 | 必填 |
| 模型部署名稱 | 必填 | 必填 |
| API 金鑰 | 必填 | 無需 |
| Azure OpenAI 資源群組名稱 | 無需 | 跨資源群組時填寫 |

Managed Identity 模式下，範本會自動嘗試為 VM 指派 `Cognitive Services OpenAI User` 角色。如果部署使用者權限不足，角色指派會失敗，但 VM 和 OpenClaw 仍然正常部署完成（Azure 入口網站可能顯示「部分失敗」）。使用者只需後續手動補上角色即可，不需要重新部署（詳見第 5 步）。

> **Azure China 使用者注意：** Azure China 環境不提供 Azure OpenAI 資源，因此 Managed Identity 模式在 Azure China 中不可用。Azure China 使用者請選擇 API Key 模式或跳過 Azure OpenAI 設定。

不需要 Azure OpenAI 則全部留空。

## 3.（選填）準備 Microsoft Teams 通道整合資訊

1. 在 Azure 入口網站中，前往 **Microsoft Entra ID**  **應用程式註冊**  **新增註冊**：
   - 名稱：任意（如 `openclaw-teams-bot`）
   - 支援的帳戶類型：選擇**僅此組織目錄中的帳戶（單一租用戶）**
   - 重新導向 URI：留空
   - 點擊**註冊**
2. 註冊完成後，記錄**應用程式（用戶端）識別碼**  即 **Teams Bot App ID**。
3. 前往**憑證和密碼**  **新增用戶端密碼**，新增密碼並記錄密碼值  即 **Teams Bot App Password**。

部署時提供以上兩個參數（要嘛全填，要嘛全部留空）。範本會自動建立 Azure Bot Service 並關聯 Teams Channel，無需手動設定。範本自動使用當前 Azure 租用戶作為 Teams tenant ID，無需手動填寫。

## 4. 部署到 Azure

### 方式 A：一鍵部署（建議）

1. 點擊上方的 **Deploy to Azure** 按鈕，登入 Azure 帳號。
2. 選擇或建立一個**資源群組 (Resource Group)**。
3. 填寫表單參數：
   - `vmName`：虛擬機器名稱
   - `adminUsername`：SSH 使用者名稱（預設 `azureuser`）
   - `sshPublicKey`：貼上第 1 步取得的 SSH 公鑰內容
   - `vmSize`：虛擬機器規格（預設 `Standard_B2as_v2`）
   - Azure OpenAI 相關參數（選填，見第 2 步）
   - Teams 通道參數（選填，見第 3 步）
4. 點擊**檢閱 + 建立**  **建立**，等待部署完成。
5. 部署完成後，點擊左側**輸出 (Outputs)**，記錄：
   - `vmPublicFqdn`：虛擬機器公用網域名稱（用於 SSH 登入）
   - `vmPrincipalId`：VM 受控識別識別碼（Managed Identity 模式需要）

### 方式 B：Azure CLI 部署

```bash
# Azure 中國區使用者先執行: az cloud set --name AzureChinaCloud
az login

az group create --name rg-openclaw --location southeastasia

# API Key 模式
az deployment group create \
  --name openclaw-deploy \
  --resource-group rg-openclaw \
  --template-uri https://raw.githubusercontent.com/hanhsia/openclaw-azure-deploy/main/azuredeploy.json \
  --parameters \
    vmName=my-openclaw \
    sshPublicKey="ssh-ed25519 AAAA..." \
    azureOpenAiAuthMode=key \
    azureOpenAiEndpoint="https://your-resource.cognitiveservices.azure.com/" \
    azureOpenAiDeployment="gpt-5.2" \
    azureOpenAiApiKey="your-api-key"

# Managed Identity 模式（建議）：省略 azureOpenAiApiKey，改 azureOpenAiAuthMode=managedIdentity
# 不接入 Azure OpenAI：省略所有 azureOpenAi* 參數
```

檢視部署輸出：
```bash
az deployment group show \
  --name openclaw-deploy \
  --resource-group rg-openclaw \
  --query properties.outputs
```

## 5.（Managed Identity 模式）部署後指派角色

如果您選擇了 Managed Identity 認證模式，範本會**自動嘗試**為 VM 的受控識別指派 `Cognitive Services OpenAI User` 角色。

- **權限足夠時（Owner / User Access Administrator）：** 角色自動指派成功，無需額外操作。
- **權限不足時（如 Contributor）：** 角色指派會失敗，Azure 入口網站可能顯示部署為「部分失敗」。但 **VM、OpenClaw、MI 代理服務全部正常運行**，不需要重新部署。您只需手動補上角色，下一次 chat 要求即可正常運作。

部署輸出中的 `azureOpenAiRoleAssignmentHint` 包含可直接複製執行的完整 `az role assignment create` 命令。

**透過 Azure 入口網站指派：**
1. 開啟 Azure OpenAI 資源  **存取控制 (IAM)**  **新增角色指派**。
2. 角色選 **Cognitive Services OpenAI User**，成員選**受控識別**，搜尋並選擇您的虛擬機器。
3. **檢閱 + 指派**。

**透過 Azure CLI 指派：**
```bash
vm_principal_id=$(az deployment group show \
  --name <deployment-name> \
  --resource-group <resource-group> \
  --query properties.outputs.vmPrincipalId.value -o tsv)

az role assignment create \
  --assignee "$vm_principal_id" \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<openai-resource-name>"
```

> 執行此命令的使用者需要 Owner、User Access Administrator 或 Role Based Access Control Administrator 角色。角色指派生效後，下一次 chat 要求即可正常運作。

## 6. SSH 登入虛擬機器

**Windows（PowerShell）：**
```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" azureuser@<vmPublicFqdn>
```

**macOS / Linux：**
```bash
ssh -i ~/.ssh/id_ed25519 azureuser@<vmPublicFqdn>
```

將 `<vmPublicFqdn>` 替換為部署輸出中的網域名稱。

## 7. 取得 Web 控制台網址並開啟瀏覽器

SSH 登入虛擬機器後，執行：
```bash
openclaw-browser-url
```

輸出範例：
```
Dashboard URL: https://your-hostname/#token=...
```

將完整 URL 複製到瀏覽器中開啟。

## 8. 瀏覽器配對授權

如果瀏覽器頁面提示 `pairing required`，**保持頁面開啟**，回到 SSH 終端執行：
```bash
openclaw-approve-browser
```

該 helper 會直接讀取本機瀏覽器配對佇列並批准最新的 Control UI 要求。如果提示沒有待處理的配對要求，請保持瀏覽器停留在配對頁面，等待幾秒後重試。命令執行完畢後，回到瀏覽器重新整理頁面即可。

> OpenClaw 上游 `2026.3.12` 到 `2026.3.13` 期間存在已知的 loopback WebSocket 交握回歸，`openclaw devices list` 可能報錯，但本範本的 `openclaw-approve-browser` 不依賴該路徑。

## 9.（選填）Teams 部署後設定

如果部署時填寫了 Teams 參數，範本已自動建立 Azure Bot Service。部署完成後，需要產生 Teams 應用程式套件並上傳到 Teams：

1. 在本機 PowerShell 中執行（需要先 clone 本儲存庫）：
   ```powershell
   ./teams-app-package/build-app-package.ps1 `
     -AppId "<Teams Bot App ID>" `
     -BotDomain "<vmPublicFqdn>"
   ```
   將 `<Teams Bot App ID>` 替換為第 3 步取得的應用程式識別碼，`<vmPublicFqdn>` 替換為部署輸出中的網域名稱。指令碼產生的 zip 檔案位於 `teams-app-package/dist/` 目錄。

2. 開啟 Microsoft Teams  左側**應用程式**  **管理您的應用程式**  **上傳自訂應用程式**，選擇產生的 zip 檔案上傳。

3. 上傳成功後，向 Bot 傳送一則私訊。Bot 會回傳一個配對碼（pairing code）。

4. SSH 登入 VM，執行以下命令完成配對：
   ```bash
   openclaw-approve-teams-pairing
   ```
   該 helper 會自動取得最新的 Teams 配對要求並批准。也可以手動傳入配對碼：
   ```bash
   openclaw-approve-teams-pairing <pairing-code>
   ```

配對完成後即可在 Teams 中正常與 Bot 對話。

## 10.（選填）後續升級

本範本使用官方 `install-cli.sh` 安裝器將 CLI 和專用 Node 執行階段裝到使用者的 `~/.openclaw` 前綴下，再透過 `openclaw onboard --non-interactive --install-daemon` 完成 gateway 安裝，最後透過 `openclaw config` 寫入 Azure 傳入的設定。

```bash
openclaw update
openclaw doctor
openclaw gateway restart
```

如果啟用了 Teams，升級後可能需要補裝擴充功能相依性：
```bash
export PATH="$HOME/.openclaw/tools/node/bin:$HOME/.openclaw/bin:$PATH"
npm install --omit=dev --prefix "$HOME/.openclaw/lib/node_modules/openclaw/extensions/msteams"
systemctl --user restart openclaw-gateway
```

如需完全重跑安裝器：
```bash
curl -fsSL https://openclaw.ai/install-cli.sh | bash -s -- --prefix "$HOME/.openclaw" --node-version 24.14.0 --no-onboard
bash -c '. /etc/openclaw/openclaw.env && openclaw onboard --non-interactive --accept-risk --mode local --workspace /data/workspace --auth-choice skip --gateway-port "$OPENCLAW_GATEWAY_PORT" --gateway-bind loopback --gateway-auth token --gateway-token "$OPENCLAW_GATEWAY_TOKEN" --install-daemon --daemon-runtime node --skip-channels --skip-skills'
bash -c '. /etc/openclaw/openclaw.env && openclaw config validate'
openclaw doctor
openclaw gateway restart
```

## 11.（選填）切換 Gateway 模式

SSH 管理員預設走本機 loopback gateway。如需切到公網 `wss://` gateway 排查問題：
```bash
openclaw-use-public-gateway
```
該 helper 會按這台 VM 的 current local device identity 去比對並自動批准對應的 pending request，然後用 `openclaw health --verbose` 驗證公網路徑可用後才持久化切換。

切回預設 loopback：
```bash
openclaw-use-loopback-gateway
```

切換後需重新連線 SSH，執行以下命令確認：
```bash
openclaw-gateway-mode current
```

## 常見問題

**SSH 報錯 `Permission denied (publickey)`**
> 私鑰與部署時使用的公鑰不符。確保使用 `-i` 指定正確的私鑰檔案。

**SSH 報錯 `UNPROTECTED PRIVATE KEY FILE`**
> 私鑰檔案權限過寬。Windows 執行 `icacls $Key /inheritance:r` 等命令修復；macOS/Linux 執行 `chmod 600 <私鑰檔案>`。

**SSH 報錯 `REMOTE HOST IDENTIFICATION HAS CHANGED!`**
> VM 重建導致主機指紋變更。執行 `ssh-keygen -R <vmPublicFqdn>` 後重新連線。

**瀏覽器報錯 `502 Bad Gateway`**
> 部署剛完成時，請等待 1-2 分鐘。如持續報錯，SSH 登入 VM 執行：
> ```bash
> sudo systemctl status openclaw-gateway caddy --no-pager
> sudo journalctl -u openclaw-gateway -n 100 --no-pager
> ```

**無法連線虛擬機器（Connection Timed Out）**
> 在 Azure 入口網站確認 VM 處於 Running 狀態、已指派公用 IP，且 NSG 允許 22 和 443 連接埠輸入。

> **環境說明：** 範本會為管理員使用者預裝 Homebrew 到 `/home/linuxbrew/.linuxbrew` 並設定 passwordless sudo。VM 作為管理員專用主機使用。

---

<a id="en"></a>
# English Deployment Guide

## 1. Prepare SSH Keys

Skip this step if you already have an SSH key pair.

**Windows (PowerShell):**
```powershell
ssh-keygen -t ed25519 -C "openclaw-azure"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

**macOS / Linux:**
```bash
ssh-keygen -t ed25519 -C "openclaw-azure"
cat ~/.ssh/id_ed25519.pub
```

Copy the public key output  you will paste it into the deployment form later.

## 2. (Optional) Prepare Azure OpenAI Information

If you want Azure OpenAI ready immediately after deployment, prepare the following based on your chosen authentication mode:

| Parameter | API Key Mode | Managed Identity Mode (Recommended) |
|-----------|-------------|-------------------------------------|
| Azure OpenAI Endpoint | Required | Required |
| Deployment Name | Required | Required |
| API Key | Required | Not needed |
| Azure OpenAI Resource Group | Not needed | When cross-resource-group |

In Managed Identity mode, the template automatically attempts to assign the `Cognitive Services OpenAI User` role to the VM. If the deploying user lacks sufficient permissions, the role assignment fails but the VM and OpenClaw are fully deployed and functional (the Azure portal may show the deployment as "partially failed"). Just assign the role manually afterward  no redeployment needed (see Step 5).

> **Azure China users:** Azure OpenAI is not available in Azure China, so Managed Identity mode cannot be used. Please choose API Key mode or skip Azure OpenAI configuration.

Leave all Azure OpenAI fields empty to skip.

## 3. (Optional) Prepare Microsoft Teams Channel Integration

1. In the Azure portal, go to **Microsoft Entra ID**  **App registrations**  **New registration**:
   - Name: any name (e.g. `openclaw-teams-bot`)
   - Supported account types: **Accounts in this organizational directory only (Single tenant)**
   - Redirect URI: leave blank
   - Click **Register**
2. After registration, note the **Application (client) ID**  this is the **Teams Bot App ID**.
3. Go to **Certificates & secrets**  **New client secret**, add a secret and note the secret value  this is the **Teams Bot App Password**.

Provide both parameters during deployment (or leave both empty). The template automatically creates the Azure Bot Service and connects the Teams Channel  no manual configuration needed. The template also uses the current Azure tenant as the Teams tenant ID.

## 4. Deploy to Azure

### Option A: One-Click Deployment (Recommended)

1. Click a **Deploy to Azure** button above and sign in.
2. Select or create a **Resource Group**.
3. Fill in the form parameters:
   - `vmName`: virtual machine name
   - `adminUsername`: SSH username (default `azureuser`)
   - `sshPublicKey`: paste the SSH public key from Step 1
   - `vmSize`: virtual machine size (default `Standard_B2as_v2`)
   - Azure OpenAI parameters (optional, see Step 2)
   - Teams channel parameters (optional, see Step 3)
4. Click **Review + create**  **Create** and wait for deployment to finish.
5. After deployment, open **Outputs** on the left and note:
   - `vmPublicFqdn`: public domain name (for SSH login)
   - `vmPrincipalId`: VM managed identity ID (needed for Managed Identity mode)

### Option B: Azure CLI Deployment

```bash
# Azure China users first run: az cloud set --name AzureChinaCloud
az login

az group create --name rg-openclaw --location southeastasia

# API Key mode
az deployment group create \
  --name openclaw-deploy \
  --resource-group rg-openclaw \
  --template-uri https://raw.githubusercontent.com/hanhsia/openclaw-azure-deploy/main/azuredeploy.json \
  --parameters \
    vmName=my-openclaw \
    sshPublicKey="ssh-ed25519 AAAA..." \
    azureOpenAiAuthMode=key \
    azureOpenAiEndpoint="https://your-resource.cognitiveservices.azure.com/" \
    azureOpenAiDeployment="gpt-5.2" \
    azureOpenAiApiKey="your-api-key"

# Managed Identity mode (recommended): omit azureOpenAiApiKey, set azureOpenAiAuthMode=managedIdentity
# Skip Azure OpenAI: omit all azureOpenAi* parameters
```

View deployment outputs:
```bash
az deployment group show \
  --name openclaw-deploy \
  --resource-group rg-openclaw \
  --query properties.outputs
```

## 5. (Managed Identity Mode) Post-Deployment Role Assignment

If you chose Managed Identity authentication, the template **automatically attempts** to assign the `Cognitive Services OpenAI User` role to the VM's managed identity.

- **When permissions are sufficient (Owner / User Access Administrator):** The role is assigned automatically. No further action needed.
- **When permissions are insufficient (e.g. Contributor):** The role assignment fails, and the Azure portal may show the deployment as "partially failed". However, **the VM, OpenClaw, and MI proxy service are all fully functional**  no redeployment is needed. Just assign the role manually, and the next chat request will work immediately.

The deployment output `azureOpenAiRoleAssignmentHint` contains the exact `az role assignment create` command you can copy and run.

**Via Azure Portal:**
1. Open your Azure OpenAI resource  **Access control (IAM)**  **Add role assignment**.
2. Select role **Cognitive Services OpenAI User**, choose **Managed identity**, search for your VM.
3. **Review + assign**.

**Via Azure CLI:**
```bash
vm_principal_id=$(az deployment group show \
  --name <deployment-name> \
  --resource-group <resource-group> \
  --query properties.outputs.vmPrincipalId.value -o tsv)

az role assignment create \
  --assignee "$vm_principal_id" \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<openai-resource-name>"
```

> The user running this command needs the Owner, User Access Administrator, or Role Based Access Control Administrator role. Once the role is assigned, the next chat request will work immediately.

## 6. SSH into the Virtual Machine

**Windows (PowerShell):**
```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" azureuser@<vmPublicFqdn>
```

**macOS / Linux:**
```bash
ssh -i ~/.ssh/id_ed25519 azureuser@<vmPublicFqdn>
```

Replace `<vmPublicFqdn>` with the domain name from the deployment outputs.

## 7. Get the Web Dashboard URL

After SSH login, run:
```bash
openclaw-browser-url
```

Example output:
```
Dashboard URL: https://your-hostname/#token=...
```

Copy the full URL and open it in your browser.

## 8. Authorize Browser Pairing

If the browser shows `pairing required`, **keep the page open**, return to SSH and run:
```bash
openclaw-approve-browser
```

This helper reads the local browser pairing queue directly and approves the newest Control UI request. If it reports no pending request, keep the browser on the pairing page, wait a few seconds, and retry. After the command succeeds, refresh the browser page.

> Known upstream note: OpenClaw `2026.3.12` through `2026.3.13` has a reported loopback WebSocket handshake regression on some hosts. The `openclaw-approve-browser` helper avoids that code path.

## 9. (Optional) Post-Deployment Teams Setup

If you provided Teams parameters during deployment, the template has already created the Azure Bot Service. After deployment, you need to generate a Teams app package and upload it to Teams:

1. Run the following in PowerShell locally (clone this repository first):
   ```powershell
   ./teams-app-package/build-app-package.ps1 `
     -AppId "<Teams Bot App ID>" `
     -BotDomain "<vmPublicFqdn>"
   ```
   Replace `<Teams Bot App ID>` with the app ID from Step 3, and `<vmPublicFqdn>` with the domain from deployment outputs. The generated zip file is in `teams-app-package/dist/`.

2. Open Microsoft Teams  **Apps** on the left  **Manage your apps**  **Upload a custom app**, and upload the generated zip file.

3. After upload, send a direct message to the bot. The bot will return a pairing code.

4. SSH into the VM and run:
   ```bash
   openclaw-approve-teams-pairing
   ```
   This helper automatically finds the latest Teams pairing request and approves it. You can also pass the pairing code manually:
   ```bash
   openclaw-approve-teams-pairing <pairing-code>
   ```

After pairing, you can chat with the bot in Teams normally.

## 10. (Optional) Updating Later

This template uses the official `install-cli.sh` installer to place the CLI and its dedicated Node runtime under the user's `~/.openclaw` prefix, then runs `openclaw onboard --non-interactive --install-daemon` to install the gateway service, and finally applies Azure-provided settings through `openclaw config`.

```bash
openclaw update
openclaw doctor
openclaw gateway restart
```

If Teams is enabled, you may need to reinstall extension dependencies after updating:
```bash
export PATH="$HOME/.openclaw/tools/node/bin:$HOME/.openclaw/bin:$PATH"
npm install --omit=dev --prefix "$HOME/.openclaw/lib/node_modules/openclaw/extensions/msteams"
systemctl --user restart openclaw-gateway
```

To rerun the installer from scratch:
```bash
curl -fsSL https://openclaw.ai/install-cli.sh | bash -s -- --prefix "$HOME/.openclaw" --node-version 24.14.0 --no-onboard
bash -c '. /etc/openclaw/openclaw.env && openclaw onboard --non-interactive --accept-risk --mode local --workspace /data/workspace --auth-choice skip --gateway-port "$OPENCLAW_GATEWAY_PORT" --gateway-bind loopback --gateway-auth token --gateway-token "$OPENCLAW_GATEWAY_TOKEN" --install-daemon --daemon-runtime node --skip-channels --skip-skills'
bash -c '. /etc/openclaw/openclaw.env && openclaw config validate'
openclaw doctor
openclaw gateway restart
```

## 11. (Optional) Switch Gateway Mode

The SSH admin shell uses the local loopback gateway by default. To switch to the public `wss://` gateway for troubleshooting:
```bash
openclaw-use-public-gateway
```
This helper matches the pending request for this VM's current local device identity, automatically approves it, validates the public path with `openclaw health --verbose`, and only then persists the switch.

Switch back to the default loopback:
```bash
openclaw-use-loopback-gateway
```

Reconnect SSH after switching and confirm with:
```bash
openclaw-gateway-mode current
```

## FAQ

**SSH reports `Permission denied (publickey)`**
> The private key does not match the public key used during deployment. Use `-i` to specify the correct private key file.

**SSH reports `UNPROTECTED PRIVATE KEY FILE`**
> Private key file permissions are too broad. On Windows, run `icacls $Key /inheritance:r` and related commands; on macOS/Linux, run `chmod 600 <key-file>`.

**SSH reports `REMOTE HOST IDENTIFICATION HAS CHANGED!`**
> The VM was recreated and the host fingerprint changed. Run `ssh-keygen -R <vmPublicFqdn>` then reconnect.

**Browser shows `502 Bad Gateway`**
> Wait 1-2 minutes after deployment finishes. If it persists, SSH into the VM and check:
> ```bash
> sudo systemctl status openclaw-gateway caddy --no-pager
> sudo journalctl -u openclaw-gateway -n 100 --no-pager
> ```

**Cannot connect to the VM (`Connection Timed Out`)**
> In Azure portal, confirm the VM is Running with a public IP, and NSG allows inbound ports 22 and 443.