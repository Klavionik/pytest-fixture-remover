# pytest fixture remove codemod
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
