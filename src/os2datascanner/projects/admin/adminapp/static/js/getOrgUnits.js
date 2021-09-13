var parameters = {};

$(function() {
    parameters['organization_id'] = document.querySelector('#id_organization').value
    getOrgUnits();

    // Eventlistener on change 
    var target = document.querySelector('#id_organization_container>.dropdown>.select-items');
    var callOnChange = new MutationObserver(function() {
        if (parameters['organization_id'] != document.querySelector('#id_organization').value){  
            parameters['organization_id'] = document.querySelector('#id_organization').value
            
            //When the organization is called, getorgunit.js removes the selected values, 
            //but not the already selected values from the variable in dropdowntree.js,
            //instead of adding another eventlistener on the same dropdown as this, we set the value to empty here
            selected_values = []

            getOrgUnits();
        }
    });
    callOnChange.observe(target, { 
        characterData: false, 
        attributes: true, 
        childList: true, 
        subtree: false 
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
            error: function (response) {
                console.log(response);
            }
        });
    }

    // Function for restructuring object to fit format of select2ToTree
    function treeify(list, idAttr, parentAttr, childrenAttr) {
        if (!idAttr) idAttr = 'uuid';
        if (!parentAttr) parentAttr = 'parent';
        if (!childrenAttr) childrenAttr = 'inc';
       
        var treeList = [];
        var lookup = {};
        list.forEach(function(obj) {
            lookup[obj[idAttr]] = obj;
            obj[childrenAttr] = [];
        });
        list.forEach(function(obj) {
            if (obj[parentAttr] != null) {
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
    };

    function insertData(result) {
        var treeArray = treeify(result)
        $("#sel_1").empty();
        $("#sel_1").select2ToTree({treeData: {dataArr:treeArray}})
    }
})
