function searchFunctionality(){
    const searchBar = document.getElementById('search-bar');
    const scannerJobList = document.getElementById('distribute-to');

searchBar.addEventListener('input', function () {
    const query = searchBar.value.toLowerCase();
    for (const scannerJob of scannerJobList.children){
      const scannerJobName = scannerJob.innerHTML.toLowerCase();

      if (scannerJobName.includes(query)){
          scannerJob.style.display = 'block';
      } else {
          scannerJob.style.display = 'none';
      }
    }
});
}
document.addEventListener('DOMContentLoaded', () => { searchFunctionality(); });