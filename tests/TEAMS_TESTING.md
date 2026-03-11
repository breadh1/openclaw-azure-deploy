# OpenClaw Azure Teams Testing

[中文](#中文) | [English](#english)

## 中文

## 前置条件

1. 已完成 [azuredeploy.json](/c:/Users/hanxia/repos/openclaw-azure-deploy/azuredeploy.json) 部署。
2. 部署时已填写 `msteamsAppId` 和 `msteamsAppPassword`。
3. 可以 SSH 登录虚拟机。
4. 已拿到 Azure Bot App ID。
5. 已知道部署输出里的公网域名或 OpenClaw 公网 URL。

## 测试步骤

### 1. 生成 Teams app package

执行：

```powershell
./teams-app-package/build-app-package.ps1 `
  -AppId "<Azure Bot App ID>" `
  -BotDomain "<你的域名或 Azure FQDN>"
```

如果 `.env` 已配置，也可以直接执行：

```powershell
./teams-app-package/build-app-package.ps1
```

输出包通常在：

```text
teams-app-package/dist/OpenClaw.zip
```

如果使用了仓库里的 Azure 集成测试产物，也可以直接用：

```text
teams-app-package/test-output/AzureCloud/OpenClaw.zip
```

### 2. 上传并安装 package

在 Teams 客户端中：

1. 打开 `Apps`。
2. 打开 `Manage your apps`。
3. 上传 ZIP 包。
4. 安装到 `Personal` scope。

### 3. 可选确认 gateway 状态

SSH 到虚拟机执行：

```bash
openclaw gateway status
```

### 4. 发送第一条 Teams 私聊

在 Teams 中找到 bot，发送第一条私聊消息。

### 5. 批准 pairing

直接执行：

```bash
openclaw-approve-teams-pairing
```

如果要批准指定 code，则执行：

```bash
openclaw-approve-teams-pairing <CODE>
```

### 6. 发送第二条 Teams 私聊

回到同一个 Teams 会话，再发送第二条消息。

### 8. 验证结果

确认第二条消息开始可以正常收到 bot 回复。

## 最短回归命令

```bash
openclaw gateway status
openclaw pairing list msteams --json
openclaw-approve-teams-pairing
openclaw pairing list msteams --json
sudo journalctl -u openclaw-gateway -n 100 --no-pager
```

## 常见情况

### 1. 第一条消息没有回复

直接执行：

```bash
openclaw-approve-teams-pairing
```

然后发送第二条消息。

### 2. 没有 pending request

先确认已经发送过第一条私聊，再执行：

```bash
openclaw pairing list msteams --json
```

### 3. 批准后没有主动通知

继续发送第二条消息，以第二条消息能正常回复为准。

---

## English

## Prerequisites

1. Deployment with [azuredeploy.json](/c:/Users/hanxia/repos/openclaw-azure-deploy/azuredeploy.json) is complete.
2. `msteamsAppId` and `msteamsAppPassword` were provided during deployment.
3. You can SSH into the VM.
4. You have the Azure Bot App ID.
5. You know the deployed public hostname or the OpenClaw public URL.

## Test Steps

### 1. Build the Teams app package

Run:

```powershell
./teams-app-package/build-app-package.ps1 `
  -AppId "<Azure Bot App ID>" `
  -BotDomain "<your domain or Azure FQDN>"
```

If `.env` is already configured, you can also run:

```powershell
./teams-app-package/build-app-package.ps1
```

The package is usually written to:

```text
teams-app-package/dist/OpenClaw.zip
```

If you are using the repo Azure integration artifacts, you can also use:

```text
teams-app-package/test-output/AzureCloud/OpenClaw.zip
```

### 2. Upload and install the package

In the Teams client:

1. Open `Apps`.
2. Open `Manage your apps`.
3. Upload the ZIP package.
4. Install it into `personal` scope.

### 3. Optionally confirm gateway status

SSH into the VM and run:

```bash
openclaw gateway status
```

### 4. Send the first Teams direct message

In Teams, find the bot and send the first direct message.

### 5. Approve pairing

Run:

```bash
openclaw-approve-teams-pairing
```

If you want to approve a specific code, run:

```bash
openclaw-approve-teams-pairing <CODE>
```

### 6. Send the second Teams direct message

Return to the same Teams chat and send the second message.

### 7. Verify the result

Confirm that the bot starts replying from the second message onward.

## Short regression command sequence

```bash
openclaw gateway status
openclaw pairing list msteams --json
openclaw-approve-teams-pairing
openclaw pairing list msteams --json
sudo journalctl -u openclaw-gateway -n 100 --no-pager
```

## Common cases

### 1. The first message gets no reply

Run:

```bash
openclaw-approve-teams-pairing
```

Then send the second message.

### 2. There is no pending request

First confirm that the first DM was sent, then run:

```bash
openclaw pairing list msteams --json
```

### 3. There is no proactive notification after approval

Send the second message and use that reply as the success criterion.
