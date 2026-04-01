"""Simple local lorem ipsum text generation utilities."""

from itertools import cycle, islice

_LOREM_SENTENCES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    "Integer nec odio praesent libero sed cursus ante dapibus diam.",
    "Nam dui ligula fringilla a euismod sodales sollicitudin vel wisi.",
    "Aenean fermentum risus id tortor fusce tellus odio dapibus id fermentum quis suscipit id erat.",
    "Etiam posuere lacus quis dolor pellentesque egestas.",
    "Curabitur vitae diam non enim vestibulum interdum.",
]


def _paragraph(sentence_count=5, offset=0):
    sentences = islice(cycle(_LOREM_SENTENCES), offset, offset + sentence_count)
    return " ".join(sentences)


def get_paragraphs(paragraph_count, sentence_count=5):
    """Return a list of lorem ipsum paragraphs.

    Args:
        paragraph_count (int): Number of paragraphs to generate.
        sentence_count (int): Number of sentences per paragraph.
    """
    paragraph_count = max(0, int(paragraph_count))
    sentence_count = max(1, int(sentence_count))
    return [_paragraph(sentence_count=sentence_count, offset=i) for i in range(paragraph_count)]
