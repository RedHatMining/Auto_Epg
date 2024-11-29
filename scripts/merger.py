import argparse
import pathlib
from xml.dom.minidom import Document, Element, parse
from collections import defaultdict
import tqdm


class ChildNodes:
    """Efficient handling of unique child elements."""

    def __init__(self, element: Element):
        self.element = element
        self.children = {}  # Keyed by (tag, attributes, text)

    def _child_key(self, element: Element) -> tuple:
        """Generate a unique key for an element."""
        tag = element.tagName if element.nodeType == element.ELEMENT_NODE else None
        text = (element.nodeValue or "").strip()
        attrs = (
            tuple(sorted((k, v) for k, v in element.attributes.items()))
            if element.attributes
            else ()
        )
        return tag, attrs, text

    def add(self, element: Element):
        """Add a unique child element."""
        key = self._child_key(element)
        if key not in self.children:
            self.children[key] = element
            self.element.appendChild(element.cloneNode(deep=True))


def merge_programs(programs: list[Element]) -> Element:
    """Merge a list of program elements into one."""
    new_element = programs[0].cloneNode(deep=True)
    children = ChildNodes(new_element)
    for program in programs[1:]:
        for child in program.childNodes:
            children.add(child)
    return new_element


def main(dom: Document, progress: bool = False):
    """Core logic for merging program data."""
    # Group programmes by (start, channel) for quick lookup
    programmes_by_key = defaultdict(list)
    for programme in dom.getElementsByTagName("programme"):
        key = (
            programme.getAttribute("start"),
            programme.getAttribute("channel"),
        )
        programmes_by_key[key].append(programme)

    # Iterate over groups and merge them
    for (start, channel), programs in tqdm.tqdm(
        programmes_by_key.items(), disable=not progress
    ):
        if len(programs) > 1:
            merged = merge_programs(programs)
            parent = programs[0].parentNode
            for program in programs:
                parent.removeChild(program)
            parent.appendChild(merged)


def entry():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(prog="merger", description="Merge program data")
    parser.add_argument(
        "--input", "-i", help="The input XMLTV file", type=pathlib.Path, required=True
    )
    parser.add_argument("output", default="-", help="The output path", nargs="?")
    args = parser.parse_args()

    with pathlib.Path(args.input).open() as file:
        dom = parse(file)

    stdout = not (args.output and args.output != "-")
    main(dom, progress=not stdout)

    result = dom.toxml(encoding="utf-8")
    if stdout:
        print(result.decode("utf-8"))
    else:
        pathlib.Path(args.output).write_bytes(result)


if __name__ == "__main__":
    entry()
