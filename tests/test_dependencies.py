from collections import OrderedDict
from inspect import Parameter

import pytest

from incant import Incanter


def test_simple_dep(incanter: Incanter):
    def func(dep1):
        return dep1 + 1

    with pytest.raises(TypeError):
        incanter.invoke(func)
    assert incanter.parameters(func) == {
        "dep1": Parameter("dep1", Parameter.POSITIONAL_OR_KEYWORD)
    }

    incanter.register_hook(lambda n, _: n == "dep1", lambda: 2)
    assert incanter.invoke(func) == 3

    assert incanter.parameters(func) == {}


def test_nested_deps(incanter: Incanter):
    incanter.register_hook(lambda n, _: n == "dep1", lambda dep2: dep2 + 1)
    incanter.register_hook(lambda n, _: n == "dep2", lambda: 2)

    def func(dep1):
        return dep1 + 1

    assert incanter.parameters(func) == {}
    assert incanter.invoke(func) == 4


def test_nested_partial_deps(incanter: Incanter):
    incanter.register_hook(
        lambda n, _: n == "dep1", lambda dep2, input: dep2 + input + 1
    )
    incanter.register_hook(lambda n, _: n == "dep2", lambda: 2)

    def func(dep1):
        return dep1 + 1

    assert incanter.parameters(func) == {
        "input": Parameter("input", Parameter.POSITIONAL_OR_KEYWORD)
    }
    assert incanter.invoke(func, 1) == 5


def test_nested_partial_deps_with_args(incanter: Incanter):
    incanter.register_hook(
        lambda n, _: n == "dep1", lambda dep2, input: dep2 + input + 1
    )
    incanter.register_hook(lambda n, _: n == "dep2", lambda: 2)

    def func(dep1, input2: float) -> float:
        return dep1 + 1 + input2

    assert incanter.parameters(func) == OrderedDict(
        [
            ("input", Parameter("input", Parameter.POSITIONAL_OR_KEYWORD)),
            (
                "input2",
                Parameter("input2", Parameter.POSITIONAL_OR_KEYWORD, annotation=float),
            ),
        ]
    )
    assert incanter.invoke(func, 1, 5.0) == 10.0


def test_shared_deps(incanter: Incanter):
    incanter.register_hook(
        lambda n, _: n == "dep1", lambda dep2, input: dep2 + input + 1
    )
    incanter.register_hook(lambda n, _: n == "dep2", lambda: 2)

    def func(dep1, input: float) -> float:
        return dep1 + 1 + input

    assert incanter.parameters(func) == OrderedDict(
        [
            (
                "input",
                Parameter("input", Parameter.POSITIONAL_OR_KEYWORD, annotation=float),
            ),
        ]
    )
    assert incanter.invoke(func, 5.0) == 14.0


def test_shared_deps_incompatible(incanter: Incanter):
    """Type incompatibilities are raised."""

    def dep1(dep2, input: str) -> str:
        return dep2 + input + "1"

    incanter.register_hook(lambda n, _: n == "dep1", dep1)
    incanter.register_hook(lambda n, _: n == "dep2", lambda: 2)

    def func(dep1, input: float) -> float:
        return dep1 + 1 + input

    with pytest.raises(Exception):
        incanter.parameters(func)

    with pytest.raises(Exception):
        incanter.invoke(func, 5.0)
