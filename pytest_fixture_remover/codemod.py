import argparse
from typing import Union

import libcst
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
                m.AtLeastN(n=1, matcher=m.Arg(m.SimpleString(f'"{self.name}"'))),
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

    def leave_Decorator(
        self, original_node: "Decorator", updated_node: "Decorator"
    ) -> Union["Decorator", FlattenSentinel["Decorator"], RemovalSentinel]:
        if m.matches(updated_node.decorator, self.get_usefixtures_matcher()):
            for child in updated_node.decorator.children:
                if m.matches(child, m.Arg(m.SimpleString(f'"{self.name}"'))):
                    node = updated_node.deep_remove(child)

                    if not len(node.decorator.args):
                        return libcst.RemoveFromParent()

                    for child_ in node.decorator.args[0].children:
                        if m.matches(child_, m.Comma()):
                            node = node.deep_remove(child_)
                    return node

        if m.matches(updated_node.decorator, self.get_parametrize_matcher()):
            # Normalize argnames from a string like "fixture,fixture1" to a
            # proper list of fixture names.
            argnames: str = updated_node.decorator.args[0].value.evaluated_value
            quote = updated_node.decorator.args[0].value.quote
            argnames_normalized = argnames.replace(quote, "").split(",")
            args_number = len(argnames_normalized)

            # The fixture in question is the only one, remove the node.
            if args_number == 1:
                return libcst.RemoveFromParent()

            # Carefully remove the fixture name from argnames,
            # construct argnames string back from the list.
            position = argnames_normalized.index(self.name)
            is_last_arg = position == len(argnames_normalized) - 1
            argnames_normalized.remove(self.name)
            new_argnames = ",".join(argnames_normalized)
            argvalues = updated_node.decorator.args[1].value

            # Remove the corresponding element from argvalues.
            comma = argvalues.elements[position].comma
            updated_node = updated_node.deep_remove(argvalues.elements[position])

            if is_last_arg:
                # If argvalue was the last, preserve its comma.
                updated_node = updated_node.with_deep_changes(
                    updated_node.decorator.args[1].value.elements[-1], comma=comma
                )

            # Set new argnames, preserving quotes.
            updated_node = updated_node.with_deep_changes(
                updated_node.decorator.args[0].value,
                value=f"{quote}{new_argnames}{quote}",
            )
        return updated_node
