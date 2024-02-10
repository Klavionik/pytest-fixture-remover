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
        return m.Call(
            func=m.Attribute(attr=m.Name("parametrize")),
            args=[
                m.Arg(m.SimpleString(f'"{self.name}"')),
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
                    if m.matches(node.decorator, m.Call(args=[])):
                        return libcst.RemoveFromParent()

                    if m.matches(node.decorator, m.Call(args=[m.DoNotCare()])):
                        for child_ in node.decorator.args[0].children:
                            if m.matches(child_, m.Comma()):
                                node = node.deep_remove(child_)
                                return node
                    return node

        if m.matches(updated_node.decorator, self.get_parametrize_matcher()):
            return libcst.RemoveFromParent()
        return updated_node
