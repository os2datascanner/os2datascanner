// add input field for user class object

var btnUserClass = document.querySelector('#btnUserClass')
var counter = 1;
var div = document.getElementById('userObjClass');
var taglist = []
var firstInput = document.querySelector('#userClass')
var inputValues = document.querySelectorAll('.user-class-input')
var hiddenInput = document.getElementsByName('user_obj_classes')[0];

// add new input field
var addInput = function() {
    counter++;
    var input = document.createElement("input");
    input.id = 'userClass' + counter;
    input.type = 'text';
    input.name = 'userClass'+ counter;
    input.className = 'user-class-input'
    div.appendChild(input);
    div.appendChild(removeUserClass(input, div));
    addUserClassInput(input);

};
btnUserClass.addEventListener('click', function() {
    addInput();
}.bind(this));

// remove button
function removeUserClass(element, parent) {
    var btnRemove = document.createElement("button");
    btnRemove.addEventListener('click', function() {
        parent.removeChild(element)
        parent.removeChild(this)
        updateTagList()
    })
    btnRemove.id = 'removeUserClass' + counter;
    btnRemove.type = 'button';
    btnRemove.name = 'removeUserClass'+ counter;
    btnRemove.textContent = 'Fjern'
    btnRemove.className += 'button--danger';
    return btnRemove
}

// update tag list on change
function addUserClassInput(element) {
    element.addEventListener('change', updateTagList)
}
function updateTagList() {
    inputValues = document.querySelectorAll('.user-class-input')
    taglist = []
    for (let i = 0; i < inputValues.length; i++) {  
        taglist.push(inputValues[i].value)
    }
    hiddenInput.value = taglist.join(', ')
}

function saveInputs() { 
    if (hiddenInput.value) {
      // dont show input field in ui (this input field contains all input values)
      hiddenInput.style.display = "none"
      inputValues[0].value = hiddenInput.value.split(",")
   } else {
      hiddenInput.style.display = "none"
   }
}

addUserClassInput(firstInput)
saveInputs()