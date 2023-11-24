// // Bar Chart start
// //
// //
// //
// //
// //
// Function for creating gradient background for each bar size.
Chart.register({
	afterUpdate: function(chart) {
		if (chart.type === 'bar'){

			// For every dataset ...
			for (var i = 0; i < chart.config.data.datasets.length; i++) {
				// We store it
				var dsMeta = chart.getDatasetMeta(i);
				var dataset = chart.config.data.datasets[i];

				// For every data in this dataset
				for (var j = 0; j < dataset.data.length; j++) {

					// We use the model to get the bottom and top border Y position
					var model = dsMeta.data[j]._model;
					var yAxis = chart.scales['y-axis-0'];
					height = Math.round(yAxis.bottom - yAxis.getPixelForValue(dataset.data[j]));
					var start = model.y;
					var end = model.y + height;


					// and to create the gradient
					gradient = chart.ctx.createLinearGradient(0, start, 0, end);

					// Make the gradient yellow if -> Find something to check for
					// TODO:
					// if (model.label !== !user) {
					// 	// The colors of the gradient that were defined in the data
					// 	gradient.addColorStop(0, dataset.backgroundColor[0][2]);
					// 	gradient.addColorStop(1, dataset.backgroundColor[0][3]);
					// }
					// else {
						// The colors of the gradient that were defined in the data
						// gradient.addColorStop(0, dataset.backgroundColor[j][0]);
						// gradient.addColorStop(1, dataset.backgroundColor[j][1]);

						//Use this instead of ^ if we need the same color every time
					gradient.addColorStop(0, dataset.backgroundColor[0][0]);
					gradient.addColorStop(1, dataset.backgroundColor[0][1]);
					// }
					// We set this new color to the data background
					model.backgroundColor = gradient;
				}
			}
		}
	}
});

// function for rounded corners
Chart.elements.Rectangle.prototype.draw = function() {
	var ctx = this._chart.ctx;
	var vm = this._view;
	var left, right, top, bottom, signX, signY, borderSkipped, radius;
	var borderWidth = vm.borderWidth;

	// If radius is less than 0 or is large enough to cause drawing errors a max
	// radius is imposed. If cornerRadius is not defined set it to 0.
	var cornerRadius = this._chart.config.options.cornerRadius;
	var fullCornerRadius = this._chart.config.options.fullCornerRadius;
	var stackedRounded = this._chart.config.options.stackedRounded;
	var typeOfChart = this._chart.config.type;

	if (cornerRadius < 0) {
		cornerRadius = 0;
	}
	if (typeof cornerRadius === 'undefined') {
		cornerRadius = 0;
	}
	if (typeof fullCornerRadius === 'undefined') {
		fullCornerRadius = false;
	}
	if (typeof stackedRounded === 'undefined') {
		stackedRounded = false;
	}

	if (!vm.horizontal) {
		// bar
		left = vm.x - vm.width / 2;
		right = vm.x + vm.width / 2;
		top = vm.y;
		bottom = vm.base;
		signX = 1;
		signY = bottom > top ? 1 : -1;
		borderSkipped = vm.borderSkipped || 'bottom';
	} else {
		// horizontal bar
		left = vm.base;
		right = vm.x;
		top = vm.y - vm.height / 2;
		bottom = vm.y + vm.height / 2;
		signX = right > left ? 1 : -1;
		signY = 1;
		borderSkipped = vm.borderSkipped || 'left';
	}

	// Canvas doesn't allow us to stroke inside the width so we can
	// adjust the sizes to fit if we're setting a stroke on the line
	if (borderWidth) {
		// borderWidth shold be less than bar width and bar height.
		var barSize = Math.min(Math.abs(left - right), Math.abs(top - bottom));
		borderWidth = borderWidth > barSize ? barSize : borderWidth;
		var halfStroke = borderWidth / 2;
		// Adjust borderWidth when bar top position is near vm.base(zero).
		var borderLeft = left + (borderSkipped !== 'left' ? halfStroke * signX : 0);
		var borderRight = right + (borderSkipped !== 'right' ? -halfStroke * signX : 0);
		var borderTop = top + (borderSkipped !== 'top' ? halfStroke * signY : 0);
		var borderBottom = bottom + (borderSkipped !== 'bottom' ? -halfStroke * signY : 0);
		// not become a vertical line?
		if (borderLeft !== borderRight) {
			top = borderTop;
			bottom = borderBottom;
		}
		// not become a horizontal line?
		if (borderTop !== borderBottom) {
			left = borderLeft;
			right = borderRight;
		}
	}

	ctx.beginPath();
	ctx.fillStyle = vm.backgroundColor;
	ctx.strokeStyle = vm.borderColor;
	ctx.lineWidth = borderWidth;

	// Corner points, from bottom-left to bottom-right clockwise
	// | 1 2 |
	// | 0 3 |
	var corners = [
		[left, bottom],
		[left, top],
		[right, top],
		[right, bottom]
	];

	// Find first (starting) corner with fallback to 'bottom'
	var borders = ['bottom', 'left', 'top', 'right'];
	var startCorner = borders.indexOf(borderSkipped, 0);
	if (startCorner === -1) {
		startCorner = 0;
	}

	function cornerAt(index) {
		return corners[(startCorner + index) % 4];
	}

	// Draw rectangle from 'startCorner'
	var corner = cornerAt(0);
	ctx.moveTo(corner[0], corner[1]);


	var nextCornerId, nextCorner, width, height, x, y;
	for (var i = 1; i < 4; i++) {
		corner = cornerAt(i);
		nextCornerId = i + 1;
		if (nextCornerId === 4) {
			nextCornerId = 0;
		}

		nextCorner = cornerAt(nextCornerId);

		width = corners[2][0] - corners[1][0];
		height = corners[0][1] - corners[1][1];
		x = corners[1][0];
		y = corners[1][1];

		var r = cornerRadius;
		// Fix radius being too large
		if (r > Math.abs(height) / 2) {
			r = Math.floor(Math.abs(height) / 2);
		}
		if (r > Math.abs(width) / 2) {
			r = Math.floor(Math.abs(width) / 2);
		}

		var xTl, xTr, yTl, yTr, xBl, xBr, yBl, yBr;
		if (height < 0) {
			// Negative values in a standard bar chart
			xTl = x;
			xTr = x + width;
			yTl = y + height;
			yTr = y + height;

			xBl = x;
			xBr = x + width;
			yBl = y;
			yBr = y;

			// Draw
			ctx.moveTo(xBl + r, yBl);

			ctx.lineTo(xBr - r, yBr);

			// bottom right
			ctx.quadraticCurveTo(xBr, yBr, xBr, yBr - r);


			ctx.lineTo(xTr, yTr + r);

			// top right
			if (fullCornerRadius) {
				ctx.quadraticCurveTo(xTr, yTr, xTr - r, yTr);
			} else {
			 	ctx.lineTo(xTr, yTr, xTr - r, yTr);	
			}

			ctx.lineTo(xTl + r, yTl);

			// top left
			if (fullCornerRadius) {
				ctx.quadraticCurveTo(xTl, yTl, xTl, yTl + r);
			} else {
				ctx.lineTo(xTl, yTl, xTl, yTl + r);
			}


			ctx.lineTo(xBl, yBl - r);

			//  bottom left
			ctx.quadraticCurveTo(xBl, yBl, xBl + r, yBl);

		} else if (width < 0) {
			// Negative values in a horizontal bar chart
			xTl = x + width;
			xTr = x;
			yTl = y;
			yTr = y;

			xBl = x + width;
			xBr = x;
			yBl = y + height;
			yBr = y + height;

			// Draw
			ctx.moveTo(xBl + radius, yBl);

			ctx.lineTo(xBr - radius, yBr);

			//  Bottom right corner
			if (fullCornerRadius) {
				ctx.quadraticCurveTo(xBr, yBr, xBr, yBr - radius);
			} else {
				ctx.lineTo(xBr, yBr, xBr, yBr - radius);
			}

			ctx.lineTo(xTr, yTr + radius);

			// top right Corner
			if (fullCornerRadius) {
				ctx.quadraticCurveTo(xTr, yTr, xTr - radius, yTr);
			} else {
				ctx.lineTo(xTr, yTr, xTr - radius, yTr);
			}

			ctx.lineTo(xTl + radius, yTl);

			// top left corner
			ctx.quadraticCurveTo(xTl, yTl, xTl, yTl + radius);

			ctx.lineTo(xBl, yBl - radius);

			//  bttom left corner
			ctx.quadraticCurveTo(xBl, yBl, xBl + radius, yBl);

		} else {

				var lastVisible = 0;
			for (var findLast = 0, findLastTo = this._chart.data.datasets.length; findLast < findLastTo; findLast++) {
				if (!this._chart.getDatasetMeta(findLast).hidden) {
					lastVisible = findLast;
				}
			}
			var rounded = this._datasetIndex === lastVisible;

			if (rounded) {
			//Positive Value
				ctx.moveTo(x + radius, y);

				ctx.lineTo(x + width - radius, y);

				// top right
				ctx.quadraticCurveTo(x + width, y, x + width, y + radius);


				ctx.lineTo(x + width, y + height - radius);

				// bottom right
				if (fullCornerRadius || typeOfChart === 'horizontalBar') {
					ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);					
				} else {
					ctx.lineTo(x + width, y + height, x + width - radius, y + height);
				}

				ctx.lineTo(x + radius, y + height);

				// bottom left
				if (fullCornerRadius) {
					ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
				} else {
					ctx.lineTo(x, y + height, x, y + height - radius);
				}

				ctx.lineTo(x, y + radius);

				// top left
				if (fullCornerRadius || typeOfChart === 'bar') {
					ctx.quadraticCurveTo(x, y, x + radius, y);
				} else {
					ctx.lineTo(x, y, x + radius, y);
				}
			}else {
				ctx.moveTo(x, y);
				ctx.lineTo(x + width, y);
				ctx.lineTo(x + width, y + height);
				ctx.lineTo(x, y + height);
				ctx.lineTo(x, y);
			}
		}
	}

	ctx.fill();
	if (borderWidth) {
		ctx.stroke();
	}
};

// Function for 'average-line'
Chart.register({
	beforeDraw: function(chart) {
		if (typeof chart.config.options.lineAt !== 'undefined') {
			var lineAt = chart.config.options.lineAt;
			var ctxPlugin = chart.ctx;
			var xAxe = chart.scales[chart.config.options.scales.xAxes[0].id];
			var yAxe = chart.scales[chart.config.options.scales.yAxes[0].id];
			ctxPlugin.strokeStyle = colorFunction('--color-grey-dark');
			ctxPlugin.lineWidth = 2;
			ctxPlugin.setLineDash([5, 5]);
			ctxPlugin.beginPath();
			lineAt = yAxe.getPixelForValue(lineAt);
			ctxPlugin.moveTo(xAxe.left, lineAt);
			ctxPlugin.lineTo(xAxe.right, lineAt);
			ctxPlugin.stroke();
		}
	}
});

// Creating data for unhandled matches bar chart

var unhandledBarChartCtx = document.querySelector("#bar_chart_unhandled").getContext('2d');

// Recieve data and create array for labels and data.

var unhandledBarChartLabels = [];
var unhandledBarChartValues = [];

for(var i = 0; i<unhandledMatches.length && i<5;i++) {
	unhandledBarChartLabels.push(unhandledMatches[i][0]);
	unhandledBarChartValues.push(unhandledMatches[i][1]);
}

// this function works for arrays with only values
var unhandledMatchesAverage = unhandledBarChartValues.reduce((a,b) => (a + b)) / unhandledBarChartValues.length;

new Chart(unhandledBarChartCtx, {
	type: 'bar',
	data: {
		labels: unhandledBarChartLabels,
		datasets: [{
			data: unhandledBarChartValues,
			backgroundColor: [
				[colorFunction('--color-primary-light'), colorFunction('--color-primary'), colorFunction('--color-warning'),colorFunction('--color-gradient-dark-yellow') ],
			],
			barThickness: 55,
		}]
	},
	options: {
		cornerRadius: 5,
		//Default: false; if true, this would round all corners of final box;
		fullCornerRadius: true,
		legend: {
			display: false
		},
		tooltips: {
			enabled: false
		},
		hover: {
			mode: null
		},
		plugins: {
		// chartjs-plugin-datalabels.min.js
			datalabels: {
				display: false
			}
		},
		scales: {
			x: {
				gridLines: {
					display: false,
					// drawOnChartArea:false
				}
			},
			y: {
				gridLines: {
						display: false,
						// drawOnChartArea:false
				},
				ticks: {
					beginAtZero: true,
					stepSize: stepSizeFunction(unhandledBarChartValues, 3),
				}
			}
		},
		lineAt: unhandledMatchesAverage, // Average line value
		responsive:true
	}
});

// Creating data for oldest matches

var oldestBarChartCtx = document.querySelector("#bar_chart_oldest").getContext('2d');

// Recieve data and create array for labels and data.

var oldestBarChartLabels = [];
var oldestBarChartValues = [];

for(var i = 0; i<oldestMatches.length && i<5;i++) {
  oldestBarChartLabels.push(oldestMatches[i][0]);
  oldestBarChartValues.push(oldestMatches[i][1]);
}

// this function works for arrays with only values
var oldestMatchesAverage = oldestBarChartValues.reduce((a,b) => (a + b)) / oldestBarChartValues.length;

new Chart(oldestBarChartCtx, {
  type: 'bar',
  data: {
    labels: oldestBarChartLabels,
    datasets: [{
      data: oldestBarChartValues,
      backgroundColor: [
        [colorFunction('--color-primary-light'), colorFunction('--color-primary')],
      ],
      barPercentage: 0.8,
    }]
  },
  options: {
    cornerRadius: 5,
    //Default: false; if true, this would round all corners of final box;
    fullCornerRadius: true,
    legend: {
      display: false
    },
    tooltips: {
      enabled: false
    },
    hover: {
      mode: null
    },
    plugins: {
    // chartjs-plugin-datalabels.min.js
      datalabels: {
        display: false
      }
    },
    scales: {
      x: {
        gridLines: {
          display: false,
          // drawOnChartArea:false
        }
      },
      y: {
        gridLines: {
            display: false,
            // drawOnChartArea:false
        },
        ticks: {
          beginAtZero: true,
          stepSize: stepSizeFunction(oldestBarChartValues, 3),
          callback: function(label) {
            return label + ' dage';
          }
        }
      }
    },
    lineAt: oldestMatchesAverage, // Average line value
    responsive:true
  }
});
