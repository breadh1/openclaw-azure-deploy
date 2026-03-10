import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = REPO_ROOT / "azuredeploy.json"

GLOBAL_CLOUD = "AzureCloud"
GLOBAL_LOCATION = "eastasia"
CHINA_CLOUD = "AzureChinaCloud"
CHINA_LOCATION = "chinanorth3"
DEFAULT_ADMIN_USERNAME = "azureuser"
DEFAULT_HOSTNAME = ""
DELETE_WAIT_TIMEOUT_SECONDS = 300
DELETE_WAIT_POLL_SECONDS = 15
SENSITIVE_PARAMETER_KEYS = {
    "azureOpenAiApiKey",
    "feishuAppSecret",
    "msteamsAppPassword",
    "sshPublicKey",
}
AZ_EXECUTABLE = shutil.which("az.cmd") or shutil.which("az") or "az"


def log_message(cloud_name, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{cloud_name}] {message}", flush=True)


def sanitize_az_args(args):
    sanitized = []
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key in SENSITIVE_PARAMETER_KEYS and value:
                sanitized.append(f"{key}=***")
                continue
        sanitized.append(arg)
    return sanitized


def stream_reader(pipe, sink, prefix, buffer):
    try:
        for line in iter(pipe.readline, ""):
            buffer.append(line)
            sink.write(f"{prefix}{line}")
            sink.flush()
    finally:
        pipe.close()


def load_env(relative_path: str):
    env = {}
    for raw_line in (
        (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    ):
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def run_az(args, cloud_name):
    command = [AZ_EXECUTABLE, *args]
    pretty_command = subprocess.list2cmdline(["az", *sanitize_az_args(args)])
    log_message(cloud_name, f"Running az command: {pretty_command}")

    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "AZURE_CORE_CLOUD": cloud_name},
    )

    stdout_buffer = []
    stderr_buffer = []
    stdout_thread = threading.Thread(
        target=stream_reader,
        args=(process.stdout, sys.stdout, f"[{cloud_name}][stdout] ", stdout_buffer),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=stream_reader,
        args=(process.stderr, sys.stderr, f"[{cloud_name}][stderr] ", stderr_buffer),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    return_code = process.wait()
    stdout_thread.join()
    stderr_thread.join()

    stdout_text = "".join(stdout_buffer)
    stderr_text = "".join(stderr_buffer)
    if return_code != 0:
        raise RuntimeError(
            f"az {' '.join(sanitize_az_args(args))} failed for {cloud_name}\nstdout:\n{stdout_text}\nstderr:\n{stderr_text}"
        )
    log_message(cloud_name, f"Completed az command: {pretty_command}")
    return stdout_text


def ensure_cloud(cloud_name):
    run_az(["cloud", "set", "--name", cloud_name], cloud_name)


def is_logged_in(cloud_name):
    try:
        ensure_cloud(cloud_name)
        run_az(["account", "show", "--output", "json"], cloud_name)
        return True
    except RuntimeError:
        return False


class AzureIntegrationDeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = load_env(".env")

    def _log(self, cloud_name, message):
        log_message(cloud_name, message)

    def _wait_for_resource_group_deletion(self, cloud_name, resource_group_name):
        deadline = time.time() + DELETE_WAIT_TIMEOUT_SECONDS
        while True:
            exists_output = run_az(
                ["group", "exists", "--name", resource_group_name],
                cloud_name,
            )
            exists = exists_output.strip().lower() == "true"
            if not exists:
                self._log(cloud_name, f"Resource group {resource_group_name} deleted")
                return

            remaining_seconds = max(0, int(deadline - time.time()))
            if remaining_seconds == 0:
                self.fail(
                    f"Timed out waiting {DELETE_WAIT_TIMEOUT_SECONDS}s for resource group {resource_group_name} deletion in {cloud_name}."
                )

            self._log(
                cloud_name,
                f"Resource group {resource_group_name} still exists; waiting {DELETE_WAIT_POLL_SECONDS}s more ({remaining_seconds}s remaining)",
            )
            time.sleep(DELETE_WAIT_POLL_SECONDS)

    def setUp(self):
        if self.env.get("TEST_RUN_INTEGRATION", "0") != "1":
            self.skipTest(
                "Set TEST_RUN_INTEGRATION=1 in .env to enable real Azure integration tests."
            )
        if not self.env.get("TEST_SSH_PUBLIC_KEY", "").strip():
            self.skipTest(
                "Set TEST_SSH_PUBLIC_KEY in .env before running integration tests."
            )

    def _deploy_and_cleanup(self, cloud_name, location, subscription_id_env_key):
        self._log(cloud_name, "Checking Azure CLI login state")
        if not is_logged_in(cloud_name):
            self.skipTest(f"Azure CLI is not logged in for {cloud_name}.")
        self._log(cloud_name, "Azure CLI login verified")

        subscription_id = self.env.get(subscription_id_env_key, "").strip()
        if subscription_id:
            self._log(cloud_name, f"Selecting subscription {subscription_id}")
            run_az(["account", "set", "--subscription", subscription_id], cloud_name)
            self._log(cloud_name, "Subscription selected")

        suffix = uuid.uuid4().hex[:8]
        resource_group_prefix = (
            self.env.get("TEST_RESOURCE_GROUP_PREFIX", "openclawtest").strip()
            or "openclawtest"
        )
        resource_group_name = f"{resource_group_prefix}-{cloud_name.lower()}-{suffix}"
        vm_name = f"openclaw{suffix}"
        rg_created = False

        parameters = [
            f"vmName={vm_name}",
            f"adminUsername={DEFAULT_ADMIN_USERNAME}",
            f"sshPublicKey={self.env['TEST_SSH_PUBLIC_KEY']}",
            f"location={location}",
            f"hostname={DEFAULT_HOSTNAME}",
        ]

        if self.env.get("TEST_FEISHU_APP_ID") and self.env.get(
            "TEST_FEISHU_APP_SECRET"
        ):
            parameters.extend(
                [
                    f"feishuAppId={self.env['TEST_FEISHU_APP_ID']}",
                    f"feishuAppSecret={self.env['TEST_FEISHU_APP_SECRET']}",
                ]
            )

        if (
            cloud_name == GLOBAL_CLOUD
            and self.env.get("TEST_MSTEAMS_APP_ID")
            and self.env.get("TEST_MSTEAMS_APP_PASSWORD")
        ):
            parameters.extend(
                [
                    f"msteamsAppId={self.env['TEST_MSTEAMS_APP_ID']}",
                    f"msteamsAppPassword={self.env['TEST_MSTEAMS_APP_PASSWORD']}",
                ]
            )

        openai_values = [
            self.env.get("TEST_AZURE_OPENAI_ENDPOINT", "").strip(),
            self.env.get("TEST_AZURE_OPENAI_DEPLOYMENT", "").strip(),
            self.env.get("TEST_AZURE_OPENAI_API_KEY", "").strip(),
        ]
        if all(openai_values):
            parameters.extend(
                [
                    f"azureOpenAiEndpoint={openai_values[0]}",
                    f"azureOpenAiDeployment={openai_values[1]}",
                    f"azureOpenAiApiKey={openai_values[2]}",
                ]
            )

        try:
            self._log(
                cloud_name,
                f"Creating resource group {resource_group_name} in {location}",
            )
            ensure_cloud(cloud_name)
            run_az(
                [
                    "group",
                    "create",
                    "--name",
                    resource_group_name,
                    "--location",
                    location,
                    "--output",
                    "json",
                ],
                cloud_name,
            )
            rg_created = True
            self._log(cloud_name, f"Resource group {resource_group_name} created")

            deployment_name = f"deploy-{suffix}"
            self._log(
                cloud_name,
                f"Starting deployment {deployment_name} for VM {vm_name}",
            )
            deployment_output = run_az(
                [
                    "deployment",
                    "group",
                    "create",
                    "--name",
                    deployment_name,
                    "--resource-group",
                    resource_group_name,
                    "--template-file",
                    str(TEMPLATE_FILE),
                    "--parameters",
                    *parameters,
                    "--output",
                    "json",
                ],
                cloud_name,
            )
            self._log(cloud_name, f"Deployment {deployment_name} completed")

            payload = json.loads(deployment_output)
            outputs = payload["properties"]["outputs"]
            vm_public_fqdn = outputs["vmPublicFqdn"]["value"]
            openclaw_public_url = outputs["openclawPublicUrl"]["value"]
            self._log(
                cloud_name,
                f"Validating outputs for {vm_public_fqdn} and {openclaw_public_url}",
            )

            expected_suffix = (
                ".cloudapp.chinacloudapi.cn"
                if cloud_name == CHINA_CLOUD
                else ".cloudapp.azure.com"
            )
            self.assertTrue(vm_public_fqdn.endswith(expected_suffix))
            self.assertTrue(openclaw_public_url.startswith("https://"))
            self.assertIn(vm_name, vm_public_fqdn)

            if cloud_name == GLOBAL_CLOUD and self.env.get("TEST_MSTEAMS_APP_ID"):
                bot_name = f"{vm_name}-bot"
                self._log(cloud_name, f"Checking Teams bot resource {bot_name}")
                bot_show = json.loads(
                    run_az(
                        [
                            "resource",
                            "show",
                            "--resource-group",
                            resource_group_name,
                            "--resource-type",
                            "Microsoft.BotService/botServices",
                            "--name",
                            bot_name,
                            "--output",
                            "json",
                        ],
                        cloud_name,
                    )
                )
                self.assertEqual(bot_show["name"], bot_name)
                self._log(cloud_name, f"Teams bot resource {bot_name} verified")

            self._log(cloud_name, "Deployment validation finished")
        finally:
            if rg_created:
                self._log(cloud_name, f"Deleting resource group {resource_group_name}")
                ensure_cloud(cloud_name)
                run_az(
                    [
                        "group",
                        "delete",
                        "--name",
                        resource_group_name,
                        "--yes",
                        "--no-wait",
                    ],
                    cloud_name,
                )
                self._log(
                    cloud_name,
                    f"Waiting for resource group {resource_group_name} deletion",
                )
                self._wait_for_resource_group_deletion(cloud_name, resource_group_name)

    def test_real_deploy_global_azure(self):
        self._deploy_and_cleanup(
            GLOBAL_CLOUD, GLOBAL_LOCATION, "TEST_GLOBAL_SUBSCRIPTION_ID"
        )

    def test_real_deploy_china_azure(self):
        self._deploy_and_cleanup(
            CHINA_CLOUD, CHINA_LOCATION, "TEST_CHINA_SUBSCRIPTION_ID"
        )


if __name__ == "__main__":
    unittest.main()
