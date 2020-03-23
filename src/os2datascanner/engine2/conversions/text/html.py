from bs4 import BeautifulSoup
from bs4.element import Tag

from ..types import OutputType
from ..registry import conversion


def _unwrap_node(n, top=False):
    if isinstance(n, Tag):
        for child in n.children:
            _unwrap_node(child)
        n.smooth()
        if not top:
            n.unwrap()


@conversion(OutputType.Text, "text/html")
def html_processor(r, **kwargs):
    with r.make_stream() as fp:
        soup = BeautifulSoup(fp, "lxml")
        if soup.body:
            _unwrap_node(soup.body, top=True)
            return " ".join(soup.body.get_text().split())
        else:
            return None
