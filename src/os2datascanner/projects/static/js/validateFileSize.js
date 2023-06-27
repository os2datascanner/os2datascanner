// jshint unused:false
function checkFileSize(inputElement, maxSizeStr) {
    let runButton = document.getElementById("run-miniscan-btn");
    let errorText = document.getElementById("file-upload-error-response").innerText;

    if (inputElement.files.length !== 1) {
        runButton.disabled = true;
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
        window.alert(errorText);
    } else {
        console.log("This is good");
        runButton.disabled = false;
    }
}
