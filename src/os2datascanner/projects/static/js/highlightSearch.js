function highlightText(query, className) {
  // Highlights all instances of the text defined by "query" in all nodes
  // with the class defined by "className".
  let nodes = document.querySelectorAll("td." + className);
  nodes.forEach(element => {
    const queryRe = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig");
    let newText = element.innerHTML;
    for (const match of element.innerHTML.matchAll(queryRe)) {
        newText = newText.replace(match[0], "<span class='text-highlight'>" + match[0] + "</span>");
    }

    if (newText.length > element.innerHTML.length) {
      element.innerHTML = newText;
    }
  });
}


htmx.onLoad(() => {
  let query = document.querySelector('#search_field').value;
  highlightText(query, 'datatable__column--name');
  highlightText(query, 'datatable__column--path');
});
