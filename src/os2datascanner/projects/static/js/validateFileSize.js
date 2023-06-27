// jshint unused:false
function checkFileSize(inputElement, maxSizeStr) {
    let runButton = document.getElementById("run-miniscan-btn");
    let errorElement = document.getElementById("file-upload-response");

    if (inputElement.files.length !== 1) {
        runButton.disabled = true;
        errorElement.style.visibility = "hidden";
        return;
    }

    const file = inputElement.files[0];
    const maxSize = +(maxSizeStr.replaceAll('.', ''));

    if (isNaN(maxSize)) {
        console.log("Warning: File size limit is not defined!");
        runButton.disabled = true;
    } else if (file.size > maxSize) {
        console.log("This is too big");
        runButton.disabled = true;
        errorElement.style.visibility = "visible";
    } else {
        console.log("This is good");
        errorElement.style.visibility = "hidden";
        runButton.disabled = false;
    }
}
