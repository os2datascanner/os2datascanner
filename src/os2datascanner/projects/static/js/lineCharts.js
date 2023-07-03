/* exported drawLine */

function makeLineChart(xdata, ydata, chartElement, xLabel = "", yLabel = "") {
	const lineChart = new Chart(chartElement, {
		type: 'line',
		data: {
			labels: xdata,
			datasets: [{
				data: ydata,
				fill: 0,
				pointRadius: 0,
				pointHitRadius: 20,
				borderWidth: 4,
				borderCapStyle: 'round',
				tension: 0,
				borderColor: "#21759c",
				pointHoverRadius: 10,
				hoverBackgroundColor: "#21759c",
			}],
		},
		options: {
			plugins: {
				tooltip: {
					enabled: true,
				},
				datalabels: {
					display: false
				},
				legend: false,
			},
			responsive: true,
			maintainAspectRatio: false,
			elements: {
				line: {
					borderJoinStyle: 'round'
				}
			},
			chartArea: {
				backgroundColor: "#f5f5f5"
			},
			scales: {
				x: {
					title: {
						
						display: xLabel !== "",
						text: xLabel,
						labelString: xLabel,
						fontSize: 16,
					},
					gridLines: {
						offsetGridLines: true,
						display: true,
						color: "#fff",
						lineWidth: 3
					},
					ticks: {
						fontSize: 16,
					},
	
				},
				y: {
					title: {
						display: yLabel !== "",
						text: yLabel,
						fontSize: 14,
					},
					gridLines: {
						display: false
					},
					ticks: {
						beginAtZero: true,
						fontSize: 14,
						stepSize: stepSizeFunction(ydata, 2),
					},
				}
			},
		}
	});

	return lineChart;
}

function drawLine(data, ctxName) {
	// Line chart
	// //
	// //
	// //
	// //
	// //
	// Creating xx line chart

	Chart.register({
		id: "chartID",
		// This works to color the background
		beforeDraw: function (chart) {

			if (chart.config.options.chartArea && chart.config.options.chartArea.backgroundColor) {
				var ctx = chart.ctx;
				var chartArea = chart.chartArea;

				var meta = chart.getDatasetMeta(0);

				// half the width of a 'bar'
				var margin = (meta.data[1]._model.x - meta.data[0]._model.x) / 2;

				// Position at index 2 - margin (index 0 is null)
				var start = meta.data[1]._model.x - margin;

				var stop = meta.data[meta.data.length - 1]._model.x - margin;

				ctx.save();
				ctx.fillStyle = chart.config.options.chartArea.backgroundColor;

				ctx.fillRect(start, chartArea.top, stop - start, chartArea.bottom - chartArea.top);
				ctx.restore();
			}
		}
	});

	var lineChartLabels = [];
	var lineChartValues = [];

	for (var i = 0; i < data.length; i++) {
		lineChartLabels.push(data[i][0].toUpperCase());
		lineChartValues.push(data[i][1]);
	}

	// Adds empty values in front of both arrays (for styling purposes)
	lineChartLabels.unshift("");
	lineChartLabels.push("");
	lineChartValues.unshift(null);
	lineChartValues.push(null);

	var lineChartCtx = document.querySelector("#line_chart_" + ctxName).getContext('2d');
	charts.push(makeLineChart(lineChartLabels, lineChartValues, lineChartCtx));
}

// Step size function
// Array = values
// steps = how many steps on y-axis ( 0 doesn't count)
var stepSizeFunction = function (array, steps) {
	"use strict";
	return (Math.ceil(Math.max.apply(null, array) / 100) * 100) / steps;
};
