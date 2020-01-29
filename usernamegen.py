#!/usr/bin/env python3

from argparse import ArgumentParser, FileType, Action, Namespace
from itertools import product
from sys import stdout
from io import TextIOWrapper
from typing import List, Set, Union, Optional, Type, Iterable
from importlib import resources as importlib_resources

import resources


def usernamegen(
    first_names: Iterable[str],
    last_names: Iterable[str],
    prefixes: Iterable[str],
    suffixes: Iterable[str],
    num_first_name_chars: int,
    num_last_name_chars: int,
    permit_aao: bool
) -> Set[str]:
    """
    Generate usernames based on first names, last names, prefixes, and suffixes.

    The generated usernames are the cartesian product of the provided first names and last names (with the specified
    number of characters extracted from the beginning of each name), prefixes, and suffixes.

    :param first_names: A collection of first names.
    :param last_names: A collection of last names.
    :param prefixes: A collection of prefixes.
    :param suffixes: A collection of suffixes.
    :param num_first_name_chars: The number of characters to extract from first names.
    :param num_last_name_chars: The number of characters to extract from last names.
    :param permit_aao: Whether to permit "åäö" in the usernames.
    :return: A set of usernames derived from the input parameters.
    """

    # If any of the iterables in the call to `itertools.product` are empty, no products will be produced. This is
    # address by the assignments below.
    first_names = first_names or ('',)
    last_names = last_names or ('',)
    prefixes = prefixes or ('',)
    suffixes = suffixes or ('',)

    translation_table = str.maketrans('åäö', 'aao')

    user_names: Set[str] = set()

    for prefix, first_name, last_name, suffix in product(prefixes, first_names, last_names, suffixes):

        first_name_part = first_name[:num_first_name_chars].strip().lower().replace('é', 'e')
        last_name_part = last_name[:num_last_name_chars].strip().lower().replace('é', 'e')

        if not permit_aao:
            first_name_part = first_name_part.translate(translation_table)
            last_name_part = last_name_part.translate(translation_table)

        if username := f'{prefix}{first_name_part}{last_name_part}{suffix}':
            user_names.add(username)

    return user_names


# TODO: Move to some other project in future?
def make_action_class(collection_name: str) -> Type[Action]:
    """
    Create an `argparse.Action` class that stores entries in a certain attribute in the `argparse` namespace.

    Supports entries in the form of strings and `argparse.FileType` file wrappers.

    :param collection_name: The name of the attribute in `argparse` namespace that is to store the entries.
    :return: A dynamically created custom `argparse.Action` class.
    """

    # NOTE: The name will not be unique.
    action_class = type(f'{collection_name}Action', (Action,), dict())

    def __call__(
        self,
        _: ArgumentParser,
        namespace: Namespace,
        values: Union[List[str], List[TextIOWrapper]],
        __: Optional[str] = None
    ) -> None:

        collected_set: Set[str] = getattr(namespace, collection_name, set())

        if isinstance(self.type, FileType):
            value_files: List[TextIOWrapper] = values
            values_to_be_added = (
                value.strip()
                for value_file in value_files
                for value in value_file.read().splitlines()
            )
        else:
            values_to_be_added = values

        collected_set.update(values_to_be_added)

        setattr(namespace, self.dest, values)
        setattr(namespace, collection_name, collected_set)

    setattr(action_class, '__call__', __call__)

    return action_class


def get_parser(
    first_names_collection_name: str,
    last_names_collection_name: str,
    prefixes_collection_name: str,
    suffixes_collection_name: str
) -> ArgumentParser:

    parser = ArgumentParser()

    parser.add_argument(
        '--num-first-name-chars',
        help='The number of characters to extract from the first names.',
        dest='num_first_name_chars',
        type=int,
        default=3,
        metavar='N'
    )

    parser.add_argument(
        '--num-last-name-chars',
        help='The number of characters to extract from the last names.',
        dest='num_last_name_chars',
        type=int,
        default=3,
        metavar='N'
    )

    parser.add_argument(
        '--permit-aao',
        help='Permit the use of åäö in usernames.',
        dest='permit_aao',
        action='store_true',
        default=False
    )

    parser.add_argument(
        '-o', '--output',
        help='A path to which the output should be written.',
        dest='output_destination',
        type=FileType('w'),
        default=stdout
    )

    parser.add_argument(
        '--first-names-files',
        help='A path of a file from which to read first names.',
        dest='first_names_files',
        type=FileType('r'),
        nargs='+',
        metavar='FIRST_NAMES_FILE',
        action=make_action_class(collection_name=first_names_collection_name)
    )

    parser.add_argument(
        '--first-names',
        help='A list of first names.',
        dest='first_names',
        nargs='+',
        metavar='FIRST_NAME',
        action=make_action_class(collection_name=first_names_collection_name)
    )

    parser.add_argument(
        '--last-names-files',
        help='A path of a file from which to read last names',
        dest='last_names_files',
        type=FileType('r'),
        nargs='+',
        metavar='LAST_NAMES_FILE',
        action=make_action_class(collection_name=last_names_collection_name)
    )

    parser.add_argument(
        '--last-names',
        help='A list of last names.',
        dest='last_names',
        nargs='+',
        metavar='LAST_NAME',
        action=make_action_class(collection_name=last_names_collection_name)
    )

    parser.add_argument(
        '--prefixes-files',
        help='A path of a file from which to read prefixes.',
        dest='prefixes_files',
        type=FileType('r'),
        nargs='+',
        metavar='PREFIXES_FILE',
        action=make_action_class(collection_name=prefixes_collection_name)
    )

    parser.add_argument(
        '--prefixes',
        help='A list of prefixes that should prefix the usernames.',
        dest='prefixes',
        nargs='+',
        metavar='PREFIX',
        action=make_action_class(collection_name=prefixes_collection_name)
    )

    parser.add_argument(
        '--suffixes-files',
        help='A path of a file from which to read suffixes.',
        dest='suffixes_files',
        type=FileType('r'),
        nargs='+',
        metavar='SUFFIXES_FILE',
        action=make_action_class(collection_name=suffixes_collection_name),
    )

    parser.add_argument(
        '--suffixes',
        help='A list of suffixes that should suffix the usernames.',
        dest='suffixes',
        nargs='+',
        metavar='SUFFIX',
        action=make_action_class(collection_name=suffixes_collection_name)
    )

    return parser


def main():
    first_names_collection_name = 'all_first_names'
    last_names_collection_name = 'all_last_names'
    prefixes_collection_name = 'all_prefixes'
    suffixes_collection_name = 'all_suffixes'

    args = get_parser(
        first_names_collection_name=first_names_collection_name,
        last_names_collection_name=last_names_collection_name,
        prefixes_collection_name=prefixes_collection_name,
        suffixes_collection_name=suffixes_collection_name
    ).parse_args()

    usernames = usernamegen(
        first_names=getattr(
            args,
            first_names_collection_name,
            set(importlib_resources.read_text(package=resources, resource='firstnames').splitlines())
        ),
        last_names=getattr(
            args,
            last_names_collection_name,
            set(importlib_resources.read_text(package=resources, resource='lastnames').splitlines())
        ),
        prefixes=getattr(args, prefixes_collection_name, ()),
        suffixes=getattr(args, suffixes_collection_name, ()),
        num_first_name_chars=args.num_first_name_chars,
        num_last_name_chars=args.num_last_name_chars,
        permit_aao=args.permit_aao
    )

    args.output_destination.write('\n'.join(usernames) + ('\n' if usernames else ''))


if __name__ == '__main__':
    main()
