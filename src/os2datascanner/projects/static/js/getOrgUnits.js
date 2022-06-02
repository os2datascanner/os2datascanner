var parameters = {};

$(function () {
    parameters.organizationId = document.querySelector('#id_organization').value;
    getOrgUnits();

    // Eventlistener on change
    document.querySelector('#id_organization').addEventListener('change', function (e) {
        var org = e.target.value;
        if (parameters.organizationId !== org) {
            parameters.organizationId = org;

            //When the organization is called, getorgunit.js removes the selected values,
            //but not the already selected values from the variable in dropdowntree.js,
            //instead of adding another eventlistener on the same dropdown as this, we set the value to empty here
            selectedValues = [];

            getOrgUnits();
        }
    });
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
    list.forEach(function (obj) {
        lookup[obj[idAttr]] = obj;
        obj[childrenAttr] = [];
    });
    list.forEach(function (obj) {
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
    isOrgUnitSelected = function () { };
    /* jshint +W021 */
    // determine wether the orginazational unit is selected
    // do not use this on add new
    if (document.location.pathname.indexOf('add') === -1) { //if not indexof
        var scannerJobId = document.location.pathname.split('/')[2];
        for (var i = 0; i < orgUnits.length; i += 1) {
            for (var j = 0; j < orgUnits[i].scanners.length; j++) {
                if (orgUnits[i].scanners[j] === parseInt(scannerJobId)) {
                    orgUnits[i].selected = "true";
                }
            }
        }
    }
}

function insertData(result) {
    isOrgUnitSelected(result);
    var treeArray = treeify(result);
    $("#sel_1").empty();
    $("#sel_1").select2ToTree({ treeData: { dataArr: treeArray } });
    // Count the number of chosen units. If any, keep the correct radio button checked.
    var orgUnits = 0;
    for (var res of result) {
        if (res.selected === "true") {
            orgUnits++;
        }
    }
    if (orgUnits > 0) {
        $("#select-org-units").prop("checked", true);
        $("#sel_1").prop("disabled", false);
    }
}
