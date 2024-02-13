# pytest fixture remove codemod
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Klavionik/pytest-fixture-remover/graph/badge.svg?token=L5GROOX2QN)](https://codecov.io/gh/Klavionik/pytest-fixture-remover)
[![PyPI - Version](https://img.shields.io/pypi/v/pytest-fixture-remover)](https://pypi.org/project/pytest-fixture-remover)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-fixture-remover)

A LibCST codemod to remove pytest fixtures applied via the `usefixtures` decorator,
as well as its parametrizations.

> [!NOTE]
> Only fixture usage will be removed, not its definition.

# Usage
This package requires Python >= 3.8. 

Install from PyPI.

```shell
pip install pytest-fixture-remover
```

Run against your tests, specifying a fixture to remove.

```shell
python -m libcst.tool codemod -x pytest_fixture_remover.RemovePytestFixtureCommand my_project_tests/ --name clean_db
```

Add `--no-format` option to stop LibCST from running Black against modified code.

Before/after examples can be found in the `tests.test_command` module.

# Note on formatting
This codemod assumes that the target code is formatted with Black using
the magic trailing comma. It **may** change the existing formatting in several ways:
1. When removing a fixture name from the `usefixtures` call.
2. When removing a value that parametrizes the fixture via `parametrize`.

In both cases the behavior is the same and obeys the following rules:
1. If there's only one item left after modifying, remove the trailing comma.
2. If there are multiple items left after modifying and the removed item was the last,
preserve the last item's comma (or its absence).
