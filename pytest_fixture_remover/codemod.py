import argparse
from typing import List, Union

import libcst as cst
from libcst import Decorator, FlattenSentinel, RemovalSentinel
from libcst import matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand


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

    def remove_fixture_usage(self, node: Decorator) -> Union[Decorator, RemovalSentinel]:
        the_only_fixture = len(node.decorator.args) == 1

        if the_only_fixture:
            return cst.RemoveFromParent()

        for child in node.decorator.children:
            if m.matches(child, m.Arg(m.SimpleString(self.name_value))):
                node = node.deep_remove(child)

                for child_ in node.decorator.args[0].children:
                    if m.matches(child_, m.Comma()):
                        node = node.deep_remove(child_)
                return node

    def remove_fixture_parametrization(self, node: Decorator) -> Union[Decorator, RemovalSentinel]:
        argnames = split_argnames(node.decorator.args[0].value.evaluated_value)
        the_only_fixture = len(argnames) == 1

        if the_only_fixture:
            return cst.RemoveFromParent()

        position = argnames.index(self.name)
        new_argnames = join_argnames([name for name in argnames if name != self.name])
        node = node.with_deep_changes(
            node.decorator.args[0].value,
            value=f'"{new_argnames}"',
        )

        # Remove the corresponding element from argvalues.
        argvalues = node.decorator.args[1].value
        comma = argvalues.elements[position].comma
        node = node.deep_remove(argvalues.elements[position])

        was_last_fixture = position == len(argnames) - 1

        if was_last_fixture:
            # If argvalue was the last, preserve its comma.
            node = node.with_deep_changes(node.decorator.args[1].value.elements[-1], comma=comma)

        return node

    def leave_Decorator(self, original_node: Decorator, updated_node: Decorator) -> Union[
        Decorator,
        FlattenSentinel[Decorator],
        RemovalSentinel,
    ]:
        if m.matches(updated_node.decorator, self.get_usefixtures_matcher()):
            return self.remove_fixture_usage(updated_node)

        if m.matches(updated_node.decorator, self.get_parametrize_matcher()):
            return self.remove_fixture_parametrization(updated_node)

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
