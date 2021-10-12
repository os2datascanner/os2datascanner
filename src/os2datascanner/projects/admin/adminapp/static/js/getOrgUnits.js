var parameters = {};

$(function() {
    parameters.organizationId = document.querySelector('#id_organization').value;
    getOrgUnits();

    // Eventlistener on change 
    var target = document.querySelector('#id_organization_container>.dropdown>.select-items');
    var callOnChange = new MutationObserver(function() {
        if (parameters.organizationId !== document.querySelector('#id_organization').value ){  
            parameters.organizationId = document.querySelector('#id_organization').value;

            //When the organization is called, getorgunit.js removes the selected values, 
            //but not the already selected values from the variable in dropdowntree.js,
            //instead of adding another eventlistener on the same dropdown as this, we set the value to empty here
            selectedValues = [];

            getOrgUnits();
        }
    });
    callOnChange.observe(target, { 
        characterData: false, 
        attributes: true, 
        childList: true, 
        subtree: false }
    );    
});

function getOrgUnits() {
    var url = $('#sel_1').attr("url");
    $.ajax({
        method: 'GET',
        url: url,
        data: parameters,
        success: function (result) {
            insertData(result);
        },
        error: function () {
            console.error("Something went wrong!");
        }
    });
}

// Function for restructuring object to fit format of select2ToTree
function treeify(list, idAttr, parentAttr, childrenAttr) {
    if (!idAttr) {
        idAttr = 'uuid';
    }
    if (!parentAttr) {
        parentAttr = 'parent';
    }
    if (!childrenAttr) {
        childrenAttr = 'inc';
    }
   
    var treeList = [];
    var lookup = {};
    list.forEach(function(obj) {
        lookup[obj[idAttr]] = obj;
        obj[childrenAttr] = [];
    });
    list.forEach(function(obj) {
        if (obj[parentAttr] !== null) {
            if (lookup[obj[parentAttr]] !== undefined) {
                lookup[obj[parentAttr]][childrenAttr].push(obj);
            } else {
                 treeList.push(obj);
            }               
        } else {
            treeList.push(obj);
        }
    });
    return treeList;
}

function isOrgUnitSelected(orgUnits) {
    // Empty the function when it's called, to make sure it's only called once
    // since we don't want to "refill" the select box, everytime a user changes organization
    /* jshint -W021 */
    isOrgUnitSelected = function(){};
    /* jshint +W021 */
    // determine wether the orginazational unit is selected
    // do not use this on add new
    if( document.location.pathname.indexOf('add') === -1){ //if not indexof
        var scannerJobId = document.location.pathname.split('/')[2];
        for(var i = 0; i < orgUnits.length; i += 1){
            for(var j = 0;j < orgUnits[i].exchangescanners.length;j += 1) {
                if(orgUnits[i].exchangescanners[j] === scannerJobId) {
                    orgUnits[i].selected = "true";
                    break;
                }
            }
        }
    }
}

function insertData(result) {
    isOrgUnitSelected(result);
    var treeArray = treeify(result);
    $("#sel_1").empty();
    $("#sel_1").select2ToTree({treeData: {dataArr:treeArray}});
}
