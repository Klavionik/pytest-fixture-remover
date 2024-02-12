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

    def test_two_fixtures_start(self) -> None:
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

    def test_two_fixtures_end(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("other_fixture", "{self._fixture_name}")
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.usefixtures("other_fixture")
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_two_fixtures_drops_trailing_comma(self) -> None:
        before = f"""
            @pytest.mark.usefixtures("other_fixture", "{self._fixture_name}",)
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.usefixtures("other_fixture")
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


class TestRemoveParametrize(CodemodTest):
    TRANSFORM = RemovePytestFixtureCommand

    @classmethod
    def setUpClass(cls):
        cls._fixture_name = "test_fixture"

    def test_the_only_argname(self):
        before = f"""
            @pytest.mark.parametrize("{self._fixture_name}", [argvalue, argvalue1])
            def test_function(param, param1):
                ...
        """
        after = """
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_two_arguments_start(self):
        before = f"""
            @pytest.mark.parametrize(
                "{self._fixture_name},other_fixture",
                [(argvalue, argvalue1), (argvalue2, argvalue3)],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "other_fixture",
                [(argvalue2, argvalue3)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_two_arguments_end(self):
        before = f"""
            @pytest.mark.parametrize(
                "other_fixture,{self._fixture_name}",
                [(argvalue, argvalue1), (argvalue2, argvalue3)],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "other_fixture",
                [(argvalue, argvalue1)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_two_arguments_end_drops_trailing_comma(self):
        before = f"""
            @pytest.mark.parametrize(
                "other_fixture,{self._fixture_name}",
                [(argvalue, argvalue1), (argvalue2, argvalue3),],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "other_fixture",
                [(argvalue, argvalue1)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_argnames_start(self):
        before = f"""
            @pytest.mark.parametrize(
                "{self._fixture_name},other_fixture,another_fixture",
                [(argvalue, argvalue1), (argvalue2, argvalue3), (argvalue4, argvalue5)],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "other_fixture,another_fixture",
                [(argvalue2, argvalue3), (argvalue4, argvalue5)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_argnames_middle(self):
        before = f"""
            @pytest.mark.parametrize(
                "first_fixture,{self._fixture_name},other_fixture",
                [(argvalue, argvalue1), (argvalue2, argvalue3), (argvalue4, argvalue5)],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "first_fixture,other_fixture",
                [(argvalue, argvalue1), (argvalue4, argvalue5)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_argnames_end(self):
        before = f"""
            @pytest.mark.parametrize(
                "first_fixture,other_fixture,{self._fixture_name}",
                [(argvalue, argvalue1), (argvalue2, argvalue3), (argvalue4, argvalue5)],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "first_fixture,other_fixture",
                [(argvalue, argvalue1), (argvalue2, argvalue3)],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)

    def test_a_few_argnames_end_keeps_trailing_comma(self):
        before = f"""
            @pytest.mark.parametrize(
                "first_fixture,other_fixture,{self._fixture_name}",
                [(argvalue, argvalue1), (argvalue2, argvalue3), (argvalue4, argvalue5),],
            )
            def test_function(param, param1):
                ...
        """
        after = """
            @pytest.mark.parametrize(
                "first_fixture,other_fixture",
                [(argvalue, argvalue1), (argvalue2, argvalue3),],
            )
            def test_function(param, param1):
                ...
        """

        self.assertCodemod(before, after, name=self._fixture_name)
