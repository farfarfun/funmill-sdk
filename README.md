# funmill-sdk

Python client SDK for the [Funmill](https://github.com/farfarfun/funmill-api) task
API. Distributed on PyPI as `funmill` and imported as `funmill.client`, sharing the
`funmill` namespace with the `funmill-api` package (`funmill.api`).

## Install

```bash
pip install funmill
```

## Usage

```python
from funmill.client import FunmillClient, TaskSubmit

with FunmillClient(base_url="http://127.0.0.1:8812", api_key="replace-me") as client:
    client.health()  # {"status": "ok", "backend": "dagu"}

    accepted = client.submit_task(
        TaskSubmit(language="python", source="def main(): return 21 * 2")
    )
    task = client.get_task(accepted.task_id)
    result = client.get_result(accepted.task_id)
```

`FunmillClient.from_env()` builds a client from `FUNMILL_URL`, `FUNMILL_API_KEY`, and
`FUNMILL_TIMEOUT` environment variables.

## API

| Method | Route |
| --- | --- |
| `health()` | `GET /health` |
| `submit_task(TaskSubmit)` | `POST /v1/tasks` |
| `submit_workflow(WorkflowSubmit)` | `POST /v1/workflows` |
| `get_task(task_id)` | `GET /v1/tasks/{task_id}` |
| `get_progress(task_id)` | `GET /v1/tasks/{task_id}/progress` |
| `get_logs(task_id)` | `GET /v1/tasks/{task_id}/logs` |
| `get_result(task_id)` | `GET /v1/tasks/{task_id}/result` |
| `cancel(task_id, reason=...)` | `POST /v1/tasks/{task_id}/cancel` |
| `rerun(task_id)` | `POST /v1/tasks/{task_id}/rerun` |

All request/response failures raise `FunmillAPIError(message, status_code)`.

## Related repositories

- [`funmill-api`](https://github.com/farfarfun/funmill-api) — the backend service
  this client talks to.
- [`funmill-dev`](https://github.com/farfarfun/funmill-dev) — the orchestration repo
  that aggregates both `funmill-api` and `funmill-sdk`.
