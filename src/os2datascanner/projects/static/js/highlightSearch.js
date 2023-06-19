function highlightText(content, query, className) {
  // Highlights all instances of the text defined by "query" in all nodes
  // with the class defined by "className".
  let nodes = content.querySelectorAll("td." + className);
  nodes.forEach(element => {
    const queryRe = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig");
    let newText = element.innerHTML;
    for (const match of element.innerHTML.matchAll(queryRe)) {
      newText = element.innerHTML.replace(match[0], "<span class='text-highlight'>" + match[0] + "</span>");
    }

    if (newText.length > element.innerHTML.length) {
      element.innerHTML = newText;
    }
  });
}


htmx.onLoad(content => {
  let query = document.querySelector('#search_field').value;
  if (query !== "") {
    // Only do the highligh search on the content, which was just loaded in.
    highlightText(content, query, 'datatable__column--name');
    highlightText(content, query, 'datatable__column--path');
  }
});
