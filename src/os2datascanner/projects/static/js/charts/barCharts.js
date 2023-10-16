function makeBarChart(chartLabels, chartDatasets, chartElement, swapXY = false, stacked = false) {
	const barChart = new Chart(chartElement, {
        type: 'bar',
        data: {
			labels: chartLabels,
			datasets: chartDatasets,
			fill: 0,
			pointRadius: 0,
			pointHitRadius: 20,
			borderCapStyle: 'round',
			tension: 0,
			pointHoverRadius: 10,
			hoverBackgroundColor: "#21759c",
		},
        options: {
			height: 200,
			// responsive: true,
            indexAxis: swapXY ? 'y' : 'x',
			plugins: {
				tooltip: {
					enabled: true,
				},
				datalabels: {
					display: false
				},
				legend: false,
				chartAreaBorder: {
					borderColor: 'gray',
					borderWidth: 1,
				},
			},
			maintainAspectRatio: false,
			scales: {
				x: {
					stacked: swapXY ? false : stacked, 
					grid: {
						display: swapXY ? true : false,
						// drawOnChartArea:false
					}
				},
				y: {
					stacked: swapXY ? stacked : false,
					grid: {
						display: swapXY ? false : true,
						// drawOnChartArea:false
					},
                    ticks: {
                        beginAtZero: true,
                        // stepSize: stepSize,
                    }
				}
			},
		},
		plugins: [
			{
				id: 'chartAreaBorder',
				beforeDraw(chart, args, options) {
				  const {ctx, chartArea: {left, top, width, height}} = chart;
				  ctx.save();
				  ctx.strokeStyle = options.borderColor;
				  ctx.lineWidth = options.borderWidth;
				  ctx.setLineDash(options.borderDash || []);
				  ctx.lineDashOffset = options.borderDashOffset;
				  ctx.strokeRect(left, top, width, height);
				  ctx.restore();
				}
			}
		]
    });

    return barChart;
}

function drawBar(data, ctxName, labels, swapXY, stacked) {
    // Bar chart
	// //
	// //
	// //
	// //
	// //
	// Creating xx bar chart

	let barChartLabels = [];
	// Array of colors, changing colors of each dataset in the graph.
	let colorArray = [ "#21759c","#d4efff", "#00496e", "#5ca4cd"];

	// NumBars is each each bar in a barchart, i.e. each month in a year, 
	// and its associated matches.
	numBars = data.length;

	// NumStacks is each dataset added, which uses the same labels for the x-axis,
	// i.e. adding both handled matches and total matches for each org-unit in an organization.
	// Both use the same x-axis; an org-unit and its data. 
	numStacks = data[0].length-1;
	let barChartDatasets = [];

	for (let i=0; i<numStacks; i++) {
		// For each dataset, we add a data-object to our array.
		barChartDatasets.push({"data": []});
		// We also add a label, as to distinguish between the data when we hover over it.
		// This might be unessecary if we only have one dataset.
		if (labels) {
			barChartDatasets[i].label = labels[i];
		}
	}

	// An array element should look like this:
	// ["Name", datasetData1, datasetData2, ..., datasetDataN]
	for (let i=0; i < numBars; i++) {
		// First position in the array should always be the x-axis label of an element,
		// i.e. January, MyOrgUnit, Username, etc.
		barChartLabels.push(data[i][0]);
		for (let j=0; j < numStacks; j++) {
			barChartDatasets[j].data.push(data[i][j+1]);
		}
	}
	// How the data should look: 
	// [["Jan", 0, 9], ["Feb", 2, 4], ["Mar", 5, 8]]
	// How the dataset should look:
	// [{'label': 'Handled matches', 'data': [0, 2, 5]}, {'label': 'Total matches', 'data': [9, 4, 8]}]

	for (let i=0; i < barChartDatasets.length; i++) {
		barChartDatasets[i].backgroundColor = colorArray[i % 4]; //Cycles colors in array
	}
	
	// let stepSize = stepSizeFunction(barChartDatasets, 2)
    let barChartCtx = document.querySelector("#bar_chart_" + ctxName).getContext('2d');

	// SwapXY switches the x and y coordinates
	// Stacked changes whether multiple datasets are positioned in front/behind each other instead
	// of next to one another. This is useful if you need to show the difference between i.e.
	// total matches of an org-unit and how many of them have been handled. 
	charts.push(makeBarChart(barChartLabels, barChartDatasets, barChartCtx, swapXY, stacked));
}

// Step size function
// Array = values
// steps = how many steps on y-axis (0 doesn't count)
// var stepSizeFunction = function (array, steps) {
// 	"use strict";
// 	return (Math.ceil(Math.max.apply(null, array) / 100) * 100) / steps
// };
