from libcst.codemod import CodemodTest

from pytest_fixture_remover.codemod import RemovePytestFixtureCommand


class TestRemoveUsage(CodemodTest):
    TRANSFORM = RemovePytestFixtureCommand

    @classmethod
    def setUpClass(cls):
        cls._fixture_name = "test_fixture"

    def test_the_only_fixture_in_use(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("{self._fixture_name}")
            def test_function(param, param1):
                ...
        """
        after = """
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_fixtures_start(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("{self._fixture_name}", "other_fixture")
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.usefixtures("other_fixture")
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_fixtures_middle(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("first_fixture", "{self._fixture_name}", "other_fixture")
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.usefixtures("first_fixture", "other_fixture")
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_fixtures_end(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("first_fixture", "{self._fixture_name}")
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.usefixtures("first_fixture")
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)
