/* exported drawBar */

function makeBarChart(chartLabels, chartDatasets, chartElement, swapXY = false, stacked = false) {
	const chartAreaBorderPlugin = {
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
	};

	const noDataTextDrawPlugin = (chartDatasets.length === 0) ? ({
		id: 'noData',
		afterDatasetsDraw(chart) {
			const {ctx, chartArea: {left, top, width, height}} = chart;
			ctx.save();
			ctx.font = 'bold 20px sans-serif';
			ctx.textAlign = 'center';
			ctx.fillText(gettext('No data available'), left + width / 2, top + height / 2);
		}
	}) : {};
	
	
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
				zoom: {
					zoom: {
						limits: {
							x: {min: 'original'}
						},
						wheel: {
							enabled: true,
							modifierKey: 'shift'
						},
						drag: {
							enabled: true,
							threshold: 20,
						},
						pinch: {
							enabled: true
						},
						mode: swapXY ? 'x' : 'y',
					}
				},
			},
			maintainAspectRatio: false,
			scales: {
				x: {
					min: 0,
					stacked: swapXY ? false : stacked, 
					grid: {
						display: swapXY ? true : false,
						// drawOnChartArea:false
					},
					ticks: {
						font: {
							size: 15
						}
					},
					grace: swapXY ? 1 : false
				},
				y: {
					min: 0,
					stacked: swapXY ? stacked : false,
					grid: {
						display: swapXY ? false : true,
						// drawOnChartArea:false
					},
                    ticks: {
                        beginAtZero: true,
						font: {
							size: 15
						}
                        // stepSize: stepSize,
                    },
					grace: swapXY ? false : 1
				}
			},
		},
		plugins: [
			chartAreaBorderPlugin,
			noDataTextDrawPlugin
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

	// NumBars is each each bar in a barchart, i.e. each month in a year, 
	// and its associated matches.
	numBars = data.length;
	//Name of the id in the template
	let barChartCtx = document.querySelector("#bar_chart_" + ctxName).getContext('2d');

	// Swift exit with empty charts, if there is no data. Writes "No data" in chart
	if(!numBars) {
		charts.push(makeBarChart([], [], barChartCtx));
		return;
	}
	
	// Array of colors, changing colors of each dataset in the graph.
	let colorArray = [ "#21759c","#d4efff", "#00496e", "#5ca4cd"];

	// NumStacks is each dataset added, which uses the same labels for the x-axis,
	// i.e. adding both handled matches and total matches for each org-unit in an organization.
	// Both use the same x-axis; an org-unit and its data. 
	let numStacks = data[0].length-1;
	// First position in the array should always be the x-axis label of an element in string,
		// i.e. January, MyOrgUnit, Username, etc.
	let barChartLabels = data.map(row => row[0]);
	let barChartDatasets = [...new Array(numStacks).keys()].map(i => ({ "data": [], "label": labels ? labels[i] : undefined }));

	// An array element should look like this:
	// ["Name", datasetData1, datasetData2, ..., datasetDataN]
	for (const i of Array(numBars).keys()) {
		for (const j of Array(numStacks).keys()) {
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

	// SwapXY switches the x and y coordinates
	// Stacked changes whether multiple datasets are positioned in front/behind each other instead
	// of next to one another. This is useful if you need to show the difference between i.e.
	// total matches of an org-unit and how many of them have been handled. 
	charts.push(makeBarChart(barChartLabels, barChartDatasets, barChartCtx, swapXY, stacked));
}

