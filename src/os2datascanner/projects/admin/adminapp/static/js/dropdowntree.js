/*    
@licstart  The following is the entire license notice for the 
JavaScript code in this page.

Copyright (C) 2016  Joseph Safwat Khella

/*!
 * Select2-to-Tree 1.1.1
 * https://github.com/clivezhg/select2-to-tree
 */
let selected_values = [];
(function ($) {
	$.fn.select2ToTree = function (options) {
		var opts = $.extend({}, options);

		if (opts.treeData) {
			buildSelect(opts.treeData, this);
		}

		opts._templateResult = opts.templateResult;
		//defines a template on how to build/rebuild the select options
		opts.templateResult = function (data, container) {
			var label = data.text;
			if (typeof opts._templateResult === "function") {
				label = opts._templateResult(data, container);
			}
			var $iteme = $("<span class='item-label'><span class='org-icon'></span></span>").append(label);
			if (data.element) {
				var ele = data.element;
				container.setAttribute("data-val", ele.value);
				if (ele.className) container.className += " " + ele.className;
				if(selected_values.indexOf(ele.value)!=-1) {
					$($iteme.children()[0]).removeClass('org-icon')
					$($iteme.children()[0]).addClass('org-icon-selected')
					container.setAttribute('aria-selected', true)
					ele.selected="selected"
				}
				if (ele.getAttribute("data-pup")) {
					container.setAttribute("data-pup", ele.getAttribute("data-pup"));
				}
				if ($(container).hasClass("non-leaf")) {
					return $.merge($('<span class="expand-collapse" onmouseup="expColMouseupHandler(event);"></span>'), $iteme);
				}
			}
			return $iteme;
		}; 
		
		// handles mouse input on tree-item, allows a parent node to expand without selecting it
		window.expColMouseupHandler = function (evt) {
			toggleSubOptions(evt.target || evt.srcElement);
			// prevent Select2 from doing "select2:selecting","select2:unselecting","select2:closing" 
			evt.stopPropagation ? evt.stopPropagation() : evt.cancelBubble = true;
			evt.preventDefault ? evt.preventDefault() : evt.returnValue = false;
		};

		opts['closeOnSelect'] = false;
		opts['shouldFocusInput'] = false;
		opts['placeholder'] = gettext('Select one or more organizational units')
    	opts['allowClear'] = true
		opts['width'] = '100%'
		var s2inst = this.select2(opts);

		// when building the tree, add all already selected values and mark them 
		s2inst.val().forEach( function(value) {
			selectNodes(value, false)
		} )

		s2inst.on("select2:open", function (evt) {
			var s2data = s2inst.data("select2");
			s2data.$dropdown.addClass("s2-to-tree");
			s2data.$dropdown.removeClass("searching-result");
			var $allsch = s2data.$dropdown.find(".select2-search__field").add(s2data.$container.find(".select2-search__field"));
			$allsch.off("input", inputHandler);
			$allsch.on("input", inputHandler);
		});

		// Show search result options even if they are collapsed 
		function inputHandler(evt) {
			var s2data = s2inst.data("select2");

			if ($(this).val().trim().length > 0) {
				s2data.$dropdown.addClass("searching-result");
			} else {
				s2data.$dropdown.removeClass("searching-result");
			}
		};

		// when unselecting a node, unselect all descendents and ancestors  
		s2inst.on('select2:unselect', function (evt) {
			let selected_id = evt.params.data.id;
			let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
			let selected_node = options.filter(function (element) { return element.dataset.val == selected_id })[0];
			//if the dropdown menu is openend, remove the checkmark
			if( selected_node ) {	
				$(selected_node.querySelector(".item-label").children[0]).removeClass('org-icon-selected')
				$(selected_node.querySelector(".item-label").children[0]).addClass('org-icon')
			}
			//finding descendents
			let descendents = [];
			findChildNodes(selected_id, descendents);
			//for each descendent, unselect select element
			descendents.forEach(function (descendent_id) {
				let child_node = options.filter(function (element) { return element.dataset.val == descendent_id })[0];
				if(  child_node ) {
					$(child_node.querySelector(".item-label").children[0]).removeClass('org-icon-selected')
					$(child_node.querySelector(".item-label").children[0]).addClass('org-icon')
					child_node.ariaSelected = false
				}
			});
			//..unselect them from selected_values			
			let to_be_removed = [selected_id]
			descendents.forEach(function (item) { to_be_removed.push(item) })
			to_be_removed.forEach(function (element) {
				selected_values = selected_values.filter(function (value) { return value != element });
			});
			changeSelectedValuesInDropdown();
		});

		// add all child nodes and the selected node
		s2inst.on('select2:selecting', function (evt) {
			let selected_id = evt.params.args.data.id;
			selectNodes(selected_id, true)
			$('.select2-search__field').val("")
			evt.preventDefault()
		});

		function selectNodes(selected_id, selectChildren) {
			selected_values.push(selected_id);
			selected_ids = [selected_id]
			
			if(selectChildren){
				let descendents = [];
				findChildNodes(selected_id, descendents);
				descendents.forEach(function (item) { selected_values.push(item) })
				descendents.forEach(function (item) { selected_ids.push(item) })
			}

			let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
			let selected_nodes = options.filter(function (option) {
				return selected_ids.indexOf(option.dataset.val)!=-1
			})
			selected_nodes.forEach( function(node) {	
				if( node.className.indexOf('non-leaf') != -1 && node.className.indexOf('opened') == -1  ) {
					$(node).addClass('opened')
					showHideSub(node)
				}
			})	

			changeSelectedValuesInDropdown();
		}

		// changes the selected values, and triggers change on tree 
		function changeSelectedValuesInDropdown() {
			unique_values = [];
			//remove duplicates
			selected_values.forEach(function (value) {
				if (unique_values.indexOf(value) == -1) 
					unique_values.push(value);
			});
			selected_values = unique_values;
			$(s2inst).val(selected_values);
			$(s2inst).trigger('change');
		}

		s2inst.on('change', function () {
			if(selected_values.length > 0) {
				let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
				let selected_nodes = options.filter(function (option) {
					return selected_values.indexOf(option.dataset.val)!=-1
				})
				selected_nodes.forEach( function(node){
					//If the dropdown elements exist
					if(node.querySelector(".item-label").children[0]) {
						$(node.querySelector(".item-label").children[0]).removeClass('org-icon')
						$(node.querySelector(".item-label").children[0]).addClass('org-icon-selected')
						node.setAttribute('aria-selected', true)
					}
				})
			}
		})

		/** finds all descendents of a node, if recursively == false, only go one lvl down */
		function findChildNodes(selected_id, descendents_ids) {
			//babel conversion for a default param
			var recursively = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : true; 
			
			var $selected_node = $('#treeview_option_' + selected_id);
			var descendents = $selected_node.data('descendents');

			if (descendents) {
				
				var regex = /\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b/; //finds all uuid's

				descendents.forEach(function (string) {
					//add all isolated uuid's to descendents_id, if not 0
					if (string.match(regex)) descendents_ids.push(string.match(regex)[0]);
				});

				if (recursively) {
					descendents_ids.forEach(function (id) {
						// recursively search down the tree for more descendents
						var temp_ids = [];
						findChildNodes(id, temp_ids);
						if (temp_ids) descendents_ids.push.apply(descendents_ids, temp_ids);
					});
				}
			}
			return descendents_ids;
		}
		return s2inst;
	};

	/* Build the Select Option elements */
	function buildSelect(treeData, $el) {

		/* Support the object path (eg: `item.label`) for 'valFld' & 'labelFld' 
		* path : 
		*/
		function readPath(object, path) {
			var currentPosition = object;
			for (var j = 0; j < path.length; j++) {
				var currentPath = path[j];
				if (currentPosition[currentPath]) {
					currentPosition = currentPosition[currentPath];
					continue;
				}
				return 'MISSING';
			}
			return currentPosition;
		}

		function buildOptions(dataArr, curLevel, pup) {
			var labelPath;
			if (treeData.labelFld && treeData.labelFld.split('.').length > 1) {
				labelPath = treeData.labelFld.split('.');
			}
			var idPath;
			if (treeData.valFld && treeData.valFld.split('.').length > 1) {
				idPath = treeData.valFld.split('.');
			}

			for (var i = 0; i < dataArr.length; i++) {
				var data = dataArr[i] || {};
				var $opt = $("<option></option>"); // the option element to be build
				if (labelPath) {
					$opt.text(readPath(data, labelPath));
				} else {
					$opt.text(data[treeData.labelFld || "name"]);
				}
				if (idPath) {
					$opt.val(readPath(data, idPath));
				} else {
					$opt.val(data[treeData.valFld || "uuid"]);
				}
				if (data[treeData.selFld || "selected"] && String(data[treeData.selFld || "selected"]) === "true") {
					$opt.prop("selected", data[treeData.selFld || "selected"]);
				}
				if ($opt.val() === "") {
					$opt.prop("disabled", true);
					$opt.val(getUniqueValue());
				} else {
					$opt.attr('id','treeview_option_' + $opt.val())
				}
				
				var inc = data[treeData.incFld || "inc"];
				if (inc && inc.length > 0) {
					var descendents = []
					inc.forEach( function(descendent) {
						descendents.push(descendent.uuid)	
					})
					$opt.data('descendents', descendents)
				}

				$opt.addClass("l" + curLevel);
				if (pup) $opt.attr("data-pup", pup);
				$el.append($opt);
				var inc = data[treeData.incFld || "inc"];
				if (inc && inc.length > 0) {
					$opt.addClass("non-leaf");
					buildOptions(inc, curLevel + 1, $opt.val());
				}
			} // end 'for'
		} // end 'buildOptions'

		buildOptions(treeData.dataArr, 1, "");
		if (treeData.dftVal) $el.val(treeData.dftVal);
	}

	var uniqueIdx = 1;
	function getUniqueValue() {
		return "autoUniqueVal_" + uniqueIdx++;
	}

	function toggleSubOptions(target) {
		$(target.parentNode).toggleClass("opened");
		showHideSub(target.parentNode);
	}

	function showHideSub(ele) {
		var curEle = ele;
		var $options = $(ele).parent(".select2-results__options");
		var shouldShow = true;
		do {
			var pup = ($(curEle).attr("data-pup") || "").replace(/'/g, "\\'");
			curEle = null;
			if (pup) {
				var pupEle = $options.find(".select2-results__option[data-val='" + pup + "']");
				if (pupEle.length > 0) {
					if (!pupEle.eq(0).hasClass("opened")) { // hide current node if any parent node is collapsed
						$(ele).removeClass("showme");
						shouldShow = false;
						break;
					}
					curEle = pupEle[0];
				}
			}
		} while (curEle);
		if (shouldShow) $(ele).addClass("showme");

		var val = ($(ele).attr("data-val") || "").replace(/'/g, "\\'");
		$options.find(".select2-results__option[data-pup='" + val + "']").each(function () {
			showHideSub(this);
		});
	}
})(jQuery);

function createTreeView() {
	/** disables file upload */
	function orgUnitSelectOptionValueToggle() {
		if (document.getElementById("sel_1")) { 
			if (document.getElementById("sel_1").value) {
				document.getElementById("id_userlist").disabled = true;
				document.getElementById("upload-file").style.backgroundColor = "#dddddd";
				document.getElementById("fileUpload").style.backgroundColor = "#dddddd";
			} else {
				document.getElementById("id_userlist").disabled = false;
				document.getElementById("upload-file").style.backgroundColor = "#fff";
			}
		}
	}
	orgUnitSelectOptionValueToggle()
	if (document.getElementById("sel_1")) { 
		document.getElementById("sel_1").onchange = function () {
			orgUnitSelectOptionValueToggle();
		}
	}
};
