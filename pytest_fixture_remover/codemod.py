import argparse
from typing import Any, List, Sequence, Union

import libcst as cst
from libcst import Decorator, FlattenSentinel, RemovalSentinel
from libcst import matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand


class Usefixtures:
    def __init__(self, node: cst.Decorator) -> None:
        self.node = node

    @property
    def fixtures(self) -> Sequence[cst.CSTNode]:
        return self.node.decorator.args

    def remove_fixture(self, fixture: cst.CSTNode) -> None:
        self.node = self.node.deep_remove(fixture)

    def mutate(self, old_node: cst.CSTNode, **changes: Any) -> None:
        self.node = self.node.with_deep_changes(old_node, **changes)


class Parametrize:
    def __init__(self, node: cst.Decorator) -> None:
        self.node = node

    @property
    def argnames(self) -> List[str]:
        return split_argnames(self.node.decorator.args[0].value.evaluated_value)

    @argnames.setter
    def argnames(self, argnames: List[str]) -> None:
        self.node = self.node.with_deep_changes(
            self.node.decorator.args[0].value,
            value=f'"{join_argnames(argnames)}"',
        )

    @property
    def argvalues(self) -> Sequence[Any]:
        return self.node.decorator.args[1].value.elements

    @argvalues.setter
    def argvalues(self, argvalues: Sequence[Any]) -> None:
        self.node = self.node.with_deep_changes(
            self.node.decorator.args[1].value,
            elements=argvalues,
        )

    def remove_argname(self, argname: str) -> None:
        self.argnames = [name for name in self.argnames if name != argname]

    def remove_argvalue(self, argvalue: Any) -> None:
        self.argvalues = [value for value in self.argvalues if value != argvalue]

    def mutate(self, old_node: cst.CSTNode, **changes: Any) -> None:
        self.node = self.node.with_deep_changes(old_node, **changes)


class RemovePytestFixtureCommand(VisitorBasedCodemodCommand):
    DESCRIPTION: str = """
        Removes usages of a pytest fixture via the `usefixtures` decorator and its parametrization.
    """

    def __init__(self, context: CodemodContext, name: str) -> None:
        super().__init__(context)
        self.name = name
        self.name_value = f'"{self.name}"'

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--name", dest="name", help="Fixture to remove.", type=str, required=True
        )

    def get_usefixtures_matcher(self) -> m.Call:
        """
        Returns a matcher for a pytest `usefixtures` call
        that has a fixture in question as one of its arguments.
        :return: Call matcher.
        """
        return m.Call(
            func=m.Attribute(attr=m.Name("usefixtures")),
            args=[
                m.ZeroOrMore(m.DoNotCare()),
                m.AtLeastN(n=1, matcher=m.Arg(m.SimpleString(self.name_value))),
                m.ZeroOrMore(m.DoNotCare()),
            ],
        )

    def get_parametrize_matcher(self) -> m.Call:
        """
        Returns a matcher for a pytest `parametrize` call
        that defines parameters for a fixture in question.
        :return: Call matcher.
        """

        def has_fixture_name(value: str) -> bool:
            return self.name in value

        return m.Call(
            func=m.Attribute(attr=m.Name("parametrize")),
            args=[
                m.Arg(m.SimpleString(m.MatchIfTrue(has_fixture_name))),
                m.ZeroOrMore(m.DoNotCare()),
            ],
        )

    def remove_fixture_usage(self, usefixtures: Usefixtures) -> Union[Decorator, RemovalSentinel]:
        the_only_fixture = len(usefixtures.fixtures) == 1

        if the_only_fixture:
            return cst.RemoveFromParent()

        for fixture in usefixtures.fixtures:
            if m.matches(fixture, m.Arg(m.SimpleString(self.name_value))):
                is_last_fixture = (
                    usefixtures.fixtures.index(fixture) == len(usefixtures.fixtures) - 1
                )
                comma = fixture.comma
                usefixtures.remove_fixture(fixture)

                # If removed fixture was the last, preserve its comma.
                if len(usefixtures.fixtures) > 1 and is_last_fixture:
                    usefixtures.mutate(usefixtures.fixtures[-1], comma=comma)
                else:
                    # If there's only one fixture name left, strip comma.
                    usefixtures.mutate(usefixtures.fixtures[-1], comma=cst.MaybeSentinel.DEFAULT)

                return usefixtures.node

    def remove_fixture_parametrization(
        self, parametrize: Parametrize
    ) -> Union[Decorator, RemovalSentinel]:
        if len(parametrize.argnames) == 1:
            return cst.RemoveFromParent()

        position = parametrize.argnames.index(self.name)
        is_last_fixture = position == len(parametrize.argnames) - 1
        parametrize.remove_argname(self.name)

        # Remove the corresponding element from argvalues.
        comma = parametrize.argvalues[position].comma
        parametrize.remove_argvalue(parametrize.argvalues[position])

        if len(parametrize.argvalues) > 1 and is_last_fixture:
            # If removed argvalue was the last, preserve its comma.
            parametrize.mutate(parametrize.argvalues[-1], comma=comma)
        else:
            # If there's only one fixture left for parametrization, strip comma.
            parametrize.mutate(parametrize.argvalues[-1], comma=cst.MaybeSentinel.DEFAULT)

        return parametrize.node

    def leave_Decorator(self, original_node: Decorator, updated_node: Decorator) -> Union[
        Decorator,
        FlattenSentinel[Decorator],
        RemovalSentinel,
    ]:
        if m.matches(updated_node.decorator, self.get_usefixtures_matcher()):
            return self.remove_fixture_usage(Usefixtures(updated_node))

        if m.matches(updated_node.decorator, self.get_parametrize_matcher()):
            return self.remove_fixture_parametrization(Parametrize(updated_node))

        return updated_node


def split_argnames(argnames_string: str) -> List[str]:
    """
    Split `parametrize` argnames string to a proper
    list of fixture names.

    >>> split_argnames("fixture,fixture1")
    ['fixture', 'fixture1']

    :param argnames_string: Argnames.
    :return: List of fixtures.
    """
    return argnames_string.split(",")


def join_argnames(argnames_list: list) -> str:
    """
    Concatecate argnames string from a list of fixture names.

    >>> join_argnames(['fixture1', 'fixture2'])
    'fixture1,fixture2'

    :param argnames_list: `pytest.mark.parametrize` argnames argument.
    :return: Fixtures string.
    """
    return ",".join(argnames_list)
