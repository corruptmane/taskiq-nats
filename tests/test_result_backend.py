import uuid
from typing import Any, List, TypeVar

import pytest
from taskiq import ResultGetError, TaskiqResult

from taskiq_nats import NATSObjectStoreResultBackend

_ReturnType = TypeVar("_ReturnType")
pytestmark = pytest.mark.anyio


class ResultForTest:
    """Just test class for testing."""

    def __init__(self) -> None:
        """Generates test class for result testing."""
        self.test_arg = uuid.uuid4()


@pytest.fixture
def task_id() -> str:
    """
    Generates ID for taskiq result.

    :returns: uuid as string.
    """
    return str(uuid.uuid4())


@pytest.fixture
def default_taskiq_result() -> TaskiqResult[Any]:
    """
    Generates default TaskiqResult.

    :returns: TaskiqResult with generic result.
    """
    return TaskiqResult(
        is_err=False,
        log=None,
        return_value="Best test ever.",
        execution_time=0.1,
    )


@pytest.fixture
def custom_taskiq_result() -> TaskiqResult[Any]:
    """
    Generates custom TaskiqResult.

    :returns: TaskiqResult with custom class result.
    """
    return TaskiqResult(
        is_err=False,
        log=None,
        return_value=ResultForTest(),
        execution_time=0.1,
    )


async def test_failure_backend_result(
    nats_result_backend: NATSObjectStoreResultBackend[_ReturnType],
    task_id: str,
) -> None:
    """Test exception raising in `get_result` method."""
    with pytest.raises(expected_exception=ResultGetError):
        await nats_result_backend.get_result(task_id=task_id)


async def test_success_backend_default_result_delete_res(
    nats_urls: List[str],
    default_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    backend: NATSObjectStoreResultBackend[_ReturnType] = NATSObjectStoreResultBackend(
        servers=nats_urls,
        keep_results=False,
    )
    await backend.startup()

    await backend.set_result(
        task_id=task_id,
        result=default_taskiq_result,
    )
    await backend.get_result(task_id=task_id)

    with pytest.raises(expected_exception=ResultGetError):
        await backend.get_result(task_id=task_id)

    await backend.shutdown()


async def test_success_backend_default_result(
    nats_result_backend: NATSObjectStoreResultBackend[_ReturnType],
    default_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """
    Tests normal behavior with default result in TaskiqResult.

    :param default_taskiq_result: TaskiqResult with default result.
    :param task_id: ID for task.
    :param nats_urls: urls to NATS.
    """
    await nats_result_backend.set_result(
        task_id=task_id,
        result=default_taskiq_result,
    )
    result = await nats_result_backend.get_result(task_id=task_id)

    assert result == default_taskiq_result


async def test_success_backend_custom_result(
    nats_result_backend: NATSObjectStoreResultBackend[_ReturnType],
    custom_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """
    Tests normal behavior with custom result in TaskiqResult.

    :param custom_taskiq_result: TaskiqResult with custom result.
    :param task_id: ID for task.
    :param redis_url: url to redis.
    """
    await nats_result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )
    result = await nats_result_backend.get_result(task_id=task_id)

    assert (
        result.return_value.test_arg  # type: ignore
        == custom_taskiq_result.return_value.test_arg  # type: ignore
    )
    assert result.is_err == custom_taskiq_result.is_err
    assert result.execution_time == custom_taskiq_result.execution_time
    assert result.log == custom_taskiq_result.log


async def test_success_backend_is_result_ready(
    nats_result_backend: NATSObjectStoreResultBackend[_ReturnType],
    custom_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """Tests `is_result_ready` method."""
    assert not await nats_result_backend.is_result_ready(task_id=task_id)
    await nats_result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )

    assert await nats_result_backend.is_result_ready(task_id=task_id)
