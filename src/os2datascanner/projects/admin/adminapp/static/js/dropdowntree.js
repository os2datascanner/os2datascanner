/*
@licstart  The following is the entire license notice for the
JavaScript code in this page.

Copyright (C) 2016  Joseph Safwat Khella

/*!
 * Select2-to-Tree 1.1.1
 * https://github.com/clivezhg/select2-to-tree
 */
let selectedValues = [];
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
				if (ele.className) {
                    container.className += " " + ele.className;
                }
				if(selectedValues.indexOf(ele.value)!==-1) {
					$($iteme.children()[0]).removeClass('org-icon');
					$($iteme.children()[0]).addClass('org-icon-selected');
					container.setAttribute('aria-selected', true);
					ele.selected="selected";
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
			/*jshint -W030 */
			evt.stopPropagation ? evt.stopPropagation() : evt.cancelBubble = true;
			evt.preventDefault ? evt.preventDefault() : evt.returnValue = false;
			/*jshint +W030 */
		};

		opts.closeOnSelect = false;
		opts.shouldFocusInput = false;
		opts.placeholder = gettext('Select one or more organizational units');
    	opts.allowClear = true;
		opts.width = 'element';
		var s2inst = this.select2(opts);

		// when building the tree, add all already selected values and mark them
		s2inst.val().forEach( function(value) {
			selectNodes(value, false);
		} );

		s2inst.on("select2:open", function () {
			var s2data = s2inst.data("select2");
			s2data.$dropdown.addClass("s2-to-tree");
			s2data.$dropdown.removeClass("searching-result");
			var $allsch = s2data.$dropdown.find(".select2-search__field").add(s2data.$container.find(".select2-search__field"));
			$allsch.off("input", inputHandler);
			$allsch.on("input", inputHandler);
		});

		// Show search result options even if they are collapsed
		function inputHandler() {
			var s2data = s2inst.data("select2");

			if ($(this).val().trim().length > 0) {
				s2data.$dropdown.addClass("searching-result");
			} else {
				s2data.$dropdown.removeClass("searching-result");
			}
		}

		// when unselecting a node, unselect all descendents and ancestors
		s2inst.on('select2:unselect', function (evt) {
			let selectedId = evt.params.data.id;
			let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
			let selectedNode = options.filter(function (element) { return element.dataset.val === selectedId; })[0];
			//if the dropdown menu is openend, remove the checkmark
			if( selectedNode ) {
				$(selectedNode.querySelector(".item-label").children[0]).removeClass('org-icon-selected');
				$(selectedNode.querySelector(".item-label").children[0]).addClass('org-icon');
			}
			//finding descendents
			let descendents = [];
			findChildNodes(selectedId, descendents);
			//for each descendent, unselect select element
			descendents.forEach(function (descendentId) {
				let childNode = options.filter(function (element) { return element.dataset.val === descendentId; })[0];
				if(  childNode ) {
					$(childNode.querySelector(".item-label").children[0]).removeClass('org-icon-selected');
					$(childNode.querySelector(".item-label").children[0]).addClass('org-icon');
					childNode.ariaSelected = false;
				}
			});
			//..unselect them from selectedValues
			let toBeRemoved = [selectedId];
			descendents.forEach(function (item) { toBeRemoved.push(item); });
			toBeRemoved.forEach(function (element) {
				selectedValues = selectedValues.filter(function (value) { return value !== element; });
			});
			changeSelectedValuesInDropdown();
		});

		// add all child nodes and the selected node
		s2inst.on('select2:selecting', function (evt) {
			let selectedId = evt.params.args.data.id;
			selectNodes(selectedId, true);
			$('.select2-search__field').val("");
			evt.preventDefault();
		});

		function selectNodes(selectedId, selectChildren) {
			selectedValues.push(selectedId);
			selectedIds = [selectedId];

			if(selectChildren){
				let descendents = [];
				findChildNodes(selectedId, descendents);
				descendents.forEach(function (item) { selectedValues.push(item); });
				descendents.forEach(function (item) { selectedIds.push(item); });
			}

			let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
			let selectedNodes = options.filter(function (option) {
				return selectedIds.indexOf(option.dataset.val)!==-1;
			});
			selectedNodes.forEach( function(node) {
				if( node.className.indexOf('non-leaf') !== -1 && node.className.indexOf('opened') === -1  ) {
					$(node).addClass('opened');
					showHideSub(node);
				}
			});

			changeSelectedValuesInDropdown();
		}

		// changes the selected values, and triggers change on tree
		function changeSelectedValuesInDropdown() {
			uniqueValues = [];
			//remove duplicates
			selectedValues.forEach(function (value) {
				if (uniqueValues.indexOf(value) === -1) {
                    uniqueValues.push(value);
                }
			});
			selectedValues = uniqueValues;
			$(s2inst).val(selectedValues);
			$(s2inst).trigger('change');
		}

		s2inst.on('change', function () {
			if(selectedValues.length > 0) {
				let options = Array.prototype.slice.call(document.querySelectorAll("li.select2-results__option"));
				let selectedNodes = options.filter(function (option) {
					return selectedValues.indexOf(option.dataset.val)!==-1;
				});
				selectedNodes.forEach( function(node){
					//If the dropdown elements exist
					if(node.querySelector(".item-label").children[0]) {
						$(node.querySelector(".item-label").children[0]).removeClass('org-icon');
						$(node.querySelector(".item-label").children[0]).addClass('org-icon-selected');
						node.setAttribute('aria-selected', true);
					}
				});
			}
		});

		/** finds all descendents of a node, if recursively === false, only go one lvl down */
		function findChildNodes(selectedId, descendentsIds) {
			//babel conversion for a default param
			var recursively = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : true;

			var $selectedNode = $('#treeview_option_' + selectedId);
			var descendents = $selectedNode.data('descendents');

			if (descendents) {

				var regex = /\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b/; //finds all uuid's

				descendents.forEach(function (string) {
					//add all isolated uuid's to descendents_id, if not 0
					if (string.match(regex)) {
                        descendentsIds.push(string.match(regex)[0]);
                    }
				});

				if (recursively) {
					descendentsIds.forEach(function (id) {
						// recursively search down the tree for more descendents
						var tempIds = [];
						findChildNodes(id, tempIds);
						if (tempIds) {
                            descendentsIds.push.apply(descendentsIds, tempIds);
                        }
					});
				}
			}
			return descendentsIds;
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
			for (var j = 0; j < path.length; j += 1) {
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

			for (var i = 0; i < dataArr.length; i += 1) {
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
					$opt.attr('id','treeview_option_' + $opt.val());
				}

				var inc = data[treeData.incFld || "inc"];
				if (inc && inc.length > 0) {
					var descendents = [];
					for (var descendent in inc) {
						if (descendent) {
						descendents.push(descendent.uuid);
						}
					}
					$opt.data('descendents', descendents);
				}

				$opt.addClass("l" + curLevel);
				if (pup) {
                    $opt.attr("data-pup", pup);
                }
				$el.append($opt);
				inc = data[treeData.incFld || "inc"];
				if (inc && inc.length > 0) {
					$opt.addClass("non-leaf");
					buildOptions(inc, curLevel + 1, $opt.val());
				}
			} // end 'for'
		} // end 'buildOptions'

		buildOptions(treeData.dataArr, 1, "");
		if (treeData.dftVal) {
            $el.val(treeData.dftVal);
        }
	}

	var uniqueIdx = 1;
	function getUniqueValue() {
		return "autoUniqueVal_" + (uniqueIdx += 1);
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
		if (shouldShow) {
            $(ele).addClass("showme");
        }

		var val = ($(ele).attr("data-val") || "").replace(/'/g, "\\'");
		$options.find(".select2-results__option[data-pup='" + val + "']").each(function () {
			showHideSub(this);
		});
	}
})(jQuery);
/* jshint -W098 */ //disable check is used ( called from other file )
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
	orgUnitSelectOptionValueToggle();
	if (document.getElementById("sel_1")) {
		document.getElementById("sel_1").onchange = function () {
			orgUnitSelectOptionValueToggle();
		};
	}
}
