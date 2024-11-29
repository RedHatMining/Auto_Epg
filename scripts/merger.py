import argparse
import pathlib
from lxml import etree
from collections import defaultdict
import tqdm


def merge_programs(programs):
    """
    Merge a list of program elements into one.
    Only unique child elements are retained.
    """
    merged = etree.Element(programs[0].tag, attrib=programs[0].attrib)
    seen = set()

    for program in programs:
        for child in program:
            key = (child.tag, frozenset(child.attrib.items()), child.text)
            if key not in seen:
                seen.add(key)
                merged.append(child)
    return merged


def main(tree, progress=False):
    """
    Core logic for merging program data.
    :param tree: The parsed XML tree
    :param progress: Whether to show a progress bar
    """
    root = tree.getroot()

    # Group programmes by (start, channel)
    programmes_by_key = defaultdict(list)
    for programme in root.findall("programme"):
        key = (programme.attrib["start"], programme.attrib["channel"])
        programmes_by_key[key].append(programme)

    # Merge and replace grouped programs
    for (start, channel), programs in tqdm.tqdm(
        programmes_by_key.items(), disable=not progress
    ):
        if len(programs) > 1:
            merged = merge_programs(programs)
            for program in programs:
                root.remove(program)
            root.append(merged)


def entry():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(prog="merger", description="Merge program data")
    parser.add_argument(
        "--input", "-i", help="The input XMLTV file", type=pathlib.Path, required=True
    )
    parser.add_argument("output", default="-", help="The output path", nargs="?")
    args = parser.parse_args()

    # Parse input XML
    tree = etree.parse(str(args.input))

    # Determine if output should go to stdout
    stdout = not (args.output and args.output != "-")
    main(tree, progress=not stdout)

    # Write output
    if stdout:
        print(etree.tostring(tree, pretty_print=True, encoding="utf-8").decode("utf-8"))
    else:
        with open(args.output, "wb") as f:
            tree.write(f, pretty_print=True, xml_declaration=True, encoding="utf-8")


if __name__ == "__main__":
    entry()
