import httpx
import pytest

from funmill.client import (
    FunmillAPIError,
    FunmillClient,
    TaskInfo,
    TaskLogs,
    TaskProgress,
    TaskResult,
    TaskStatus,
    TaskSubmit,
    WorkflowSubmit,
)

JOB_ID = "job-1"
RERUN_ID = "job-2"
API_KEY = "secret"


def workflow() -> WorkflowSubmit:
    return WorkflowSubmit(
        tasks=[
            {"key": "a", "language": "python", "source": "def main(): return 1"},
            {
                "key": "b",
                "language": "python",
                "source": "def main(): return 2",
                "depends_on": ["a"],
            },
        ]
    )


def make_client(handler) -> FunmillClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        base_url="http://testserver",
        transport=transport,
        headers={"X-API-Key": API_KEY},
    )
    return FunmillClient(
        base_url="http://testserver", api_key=API_KEY, client=http_client
    )


def test_client_covers_every_http_route():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == API_KEY
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "backend": "dagu"})
        if request.url.path == "/v1/tasks" and request.method == "POST":
            return httpx.Response(
                200, json={"task_id": JOB_ID, "status": "queued", "rerun_of": None}
            )
        if request.url.path == "/v1/workflows":
            return httpx.Response(
                200, json={"task_id": JOB_ID, "status": "queued", "rerun_of": None}
            )
        if request.url.path == f"/v1/tasks/{JOB_ID}" and request.method == "GET":
            return httpx.Response(200, json={"task_id": JOB_ID, "status": "succeeded"})
        if request.url.path == f"/v1/tasks/{JOB_ID}/progress":
            return httpx.Response(200, json={"task_id": JOB_ID, "progress": 100})
        if request.url.path == f"/v1/tasks/{JOB_ID}/logs":
            return httpx.Response(200, json={"task_id": JOB_ID, "logs": "done"})
        if request.url.path == f"/v1/tasks/{JOB_ID}/result":
            return httpx.Response(200, json={"task_id": JOB_ID, "result": {"ok": True}})
        if request.url.path == f"/v1/tasks/{JOB_ID}/cancel":
            return httpx.Response(200, json={})
        if request.url.path == f"/v1/tasks/{JOB_ID}/rerun":
            return httpx.Response(
                200,
                json={"task_id": RERUN_ID, "status": "queued", "rerun_of": JOB_ID},
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url.path}")

    with make_client(handler) as sdk:
        assert sdk.health() == {"status": "ok", "backend": "dagu"}

        submitted = TaskSubmit(language="python", source="def main(): pass")
        accepted = sdk.submit_task(submitted)
        assert accepted.task_id == JOB_ID
        assert accepted.status == TaskStatus.QUEUED

        accepted = sdk.submit_workflow(workflow())
        assert accepted.task_id == JOB_ID

        assert sdk.get_task(JOB_ID) == TaskInfo(
            task_id=JOB_ID, status=TaskStatus.SUCCEEDED
        )
        assert sdk.get_progress(JOB_ID) == TaskProgress(task_id=JOB_ID, progress=100)
        assert sdk.get_logs(JOB_ID) == TaskLogs(task_id=JOB_ID, logs="done")
        assert sdk.get_result(JOB_ID) == TaskResult(task_id=JOB_ID, result={"ok": True})

        assert sdk.cancel(JOB_ID) is None

        rerun = sdk.rerun(JOB_ID)
        assert rerun.task_id == RERUN_ID
        assert rerun.rerun_of == JOB_ID


def test_client_surfaces_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "invalid api key"})

    with make_client(handler) as sdk:
        with pytest.raises(FunmillAPIError) as excinfo:
            sdk.get_task(JOB_ID)
        assert excinfo.value.status_code == 401
        assert "invalid api key" in str(excinfo.value)


def test_client_surfaces_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with make_client(handler) as sdk:
        with pytest.raises(FunmillAPIError) as excinfo:
            sdk.get_task(JOB_ID)
        assert excinfo.value.status_code == 504


def test_client_surfaces_connection_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with make_client(handler) as sdk:
        with pytest.raises(FunmillAPIError) as excinfo:
            sdk.get_task(JOB_ID)
        assert excinfo.value.status_code == 502
