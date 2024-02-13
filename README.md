# pytest fixture remove codemod
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Klavionik/pytest-fixture-remover/graph/badge.svg?token=L5GROOX2QN)](https://codecov.io/gh/Klavionik/pytest-fixture-remover)
[![PyPI - Version](https://img.shields.io/pypi/v/pytest-fixture-remover)](https://pypi.org/project/pytest-fixture-remover)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-fixture-remover)

A LibCST codemod to remove pytest fixtures applied via the `usefixtures` decorator,
as well as its parametrizations.

> [!NOTE]
> Only fixture usages will be removed, not its definition.

# Usage
This package requires Python >= 3.8. 

Install from PyPI into your project.

```shell
pip install pytest-fixture-remover
```

Run against your tests, specifying a fixture to remove.

```shell
python -m libcst.tool codemod.RemovePytestFixtureCommand my_project_tests/ --name clean_db
```

Before/after examples can be found in the `tests.test_command` module.
