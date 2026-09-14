import pytest

from cortex.benchmarks.errors import LeakageError
from cortex.benchmarks.runner import guard_case

from .helpers import make_case


def test_future_event_is_rejected():
    case = make_case()
    case.history[0].events[0].timestamp = "2027-01-01T00:00:00Z"
    with pytest.raises(LeakageError):
        guard_case(case)
