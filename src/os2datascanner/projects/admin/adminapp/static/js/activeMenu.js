/**
 * Set active link in the sidebar menu
 *
 * @param {object} aObj   All a tag links in the sidebar menu.
 */
function setActive() {
  aObj = document.getElementById('navigation').getElementsByTagName('a');
  for(i=0;i<aObj.length;i += 1) {
    // Loop over all a tags.
    if(document.location.href.indexOf(aObj[i].href)>=0) {
      // if the a tag is clicked add active to the link.
      aObj[i].className='active';
    }
  }
}

window.onload = setActive;
