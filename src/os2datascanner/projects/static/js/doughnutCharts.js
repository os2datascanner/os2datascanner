/* exported drawDoughnuts */

function makeDoughnutChart(text, data, colors, chartElement) {
	const doughnutChart = new Chart(chartElement, {
		type: 'doughnut',
		data: {
			datasets: [{
				data: data,
				backgroundColor: colors,
				borderWidth: 0
			}]
		},
		options: {
			cutoutPercentage: 75,
			elements: {
				arc: {
					roundedCornersFor: 0
				},
				center: {
					minFontSize: 20,
					maxFontSize: 20,
					weight: 'bold',
					text: text,
				}
			},
			plugins: {
				datalabels: {
					display: false
				},
			},
			events: [],
			responsive: true,
			aspectRatio: 1,
			maintainAspectRatio: false
		}
	});

	return doughnutChart;
}

function drawDoughnuts(sensitivities, totalHandledMatches, totalMatches, handledPercentage) {
	// Doughnut chart
	// //
	// //
	// //
	// //
	// //
	// function for rounded corners
	Chart.pluginService.register({
		afterUpdate: function (chart) {
			if (chart.config.options.elements.arc.roundedCornersFor !== undefined) {
				var arc = chart.getDatasetMeta(0).data[chart.config.options.elements.arc.roundedCornersFor];
				arc.round = {
					x: (chart.chartArea.left + chart.chartArea.right) / 2,
					y: (chart.chartArea.top + chart.chartArea.bottom) / 2,
					radius: (chart.outerRadius + chart.innerRadius) / 2,
					thickness: (chart.outerRadius - chart.innerRadius) / 2 - 1,
					backgroundColor: arc._model.backgroundColor
				};
			}
		},

		afterDraw: function (chart) {
			if (chart.config.options.elements.arc.roundedCornersFor !== undefined) {
				var ctx = chart.chart.ctx;
				var arc = chart.getDatasetMeta(0).data[chart.config.options.elements.arc.roundedCornersFor];
				var startAngle = Math.PI / 2 - arc._view.startAngle;
				var endAngle = Math.PI / 2 - arc._view.endAngle;

				ctx.save();
				ctx.translate(arc.round.x, arc.round.y);
				ctx.fillStyle = arc.round.backgroundColor;
				ctx.beginPath();
				ctx.arc(arc.round.radius * Math.sin(startAngle), arc.round.radius * Math.cos(startAngle), arc.round.thickness, 0, 2 * Math.PI);
				ctx.arc(arc.round.radius * Math.sin(endAngle), arc.round.radius * Math.cos(endAngle), arc.round.thickness, 0, 2 * Math.PI);
				ctx.closePath();
				ctx.fill();
				ctx.restore();
			}
		},
	});

	// http://jsfiddle.net/kdvuxbtj/

	// function for moving label to center of chart
	Chart.pluginService.register({
		beforeDraw: function (chart) {
			if (chart.config.type === 'doughnut') {
				var ctx, centerConfig, fontStyle, txt, weight, color, maxFontSize, sidePadding, sidePaddingCalculated;
				if (chart.config.options.elements.center) {
					// Get ctx from string
					ctx = chart.chart.ctx;

					// Get options from the center object in options
					centerConfig = chart.config.options.elements.center;
					fontStyle = centerConfig.fontStyle || 'Arial';
					txt = centerConfig.text;
					weight = centerConfig.weight;
					color = centerConfig.color || '#000';
					maxFontSize = centerConfig.maxFontSize || 75;
					sidePadding = centerConfig.sidePadding || 20;
					sidePaddingCalculated = (sidePadding / 100) * (chart.innerRadius * 2);
					// Start with a base font of 30px
					ctx.font = weight + " 30px " + fontStyle;
				}

				// Get the width of the string and also the width of the element minus 10 to give it 5px side padding
				var stringWidth = ctx.measureText(txt).width;
				var elementWidth = (chart.innerRadius * 2) - sidePaddingCalculated;

				// Find out how much the font can grow in width.
				var widthRatio = elementWidth / stringWidth;
				var newFontSize = Math.floor(30 * widthRatio);
				var elementHeight = (chart.innerRadius * 2);

				// Pick a new font size so it will not be larger than the height of label.
				var fontSizeToUse = Math.min(newFontSize, elementHeight, maxFontSize);
				var minFontSize = centerConfig.minFontSize;
				var lineHeight = centerConfig.lineHeight || 25;
				var wrapText = false;

				if (minFontSize === undefined) {
					minFontSize = 20;
				}

				if (minFontSize && fontSizeToUse < minFontSize) {
					fontSizeToUse = minFontSize;
					wrapText = true;
				}

				// Set font settings to draw it correctly.
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
				var centerX = ((chart.chartArea.left + chart.chartArea.right) / 2);
				var centerY = ((chart.chartArea.top + chart.chartArea.bottom) / 2);
				ctx.font = weight + ' ' + fontSizeToUse + "px " + fontStyle;
				ctx.fillStyle = color;

				if (!wrapText) {
					ctx.fillText(txt, centerX, centerY);
					return;
				}

				var words = txt.split(' ');
				var line = '';
				var lines = [];

				// Break words up into multiple lines if necessary
				for (var n = 0; n < words.length; n++) {
					var testLine = line + words[n] + ' ';
					var metrics = ctx.measureText(testLine);
					var testWidth = metrics.width;
					if (testWidth > elementWidth && n > 0) {
						lines.push(line);
						line = words[n] + ' ';
					} else {
						line = testLine;
					}
				}

				// Move the center up depending on line height and number of lines
				centerY -= (lines.length / 2) * lineHeight;

				for (var m = 0; m < lines.length; m++) {
					ctx.fillText(lines[m], centerX, centerY);
					centerY += lineHeight;
				}
				//Draw text in center
				ctx.fillText(line, centerX, centerY);
			}
		}
	});
	var handledMatches = JSON.parse(document.getElementById('handled_matches').textContent);
	var criticalHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_critical").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		avoidZero(handledMatches[0][1], sensitivities[0][1]),
		// Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100.
		// This is so that the secondary color will fill the whole graph
		// this could be prettier, if we 'pre-calculated' the %
		[handledMatches[0][1], ((!sensitivities[0][1]) && (!handledMatches[0][1])) ? 100 : sensitivities[0][1] - handledMatches[0][1]],
		['#e24e4e', '#f5f5f5'],
		criticalHandledDoughnutChartCtx
	));

	var problemHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_problem").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		avoidZero(handledMatches[1][1], sensitivities[1][1]),
		// Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100.
		// This is so that the secondary color will fill the whole graph
		// this could be prettier, if we 'pre-calculated' the %
		[handledMatches[1][1], ((!sensitivities[1][1]) && (!handledMatches[1][1])) ? 100 : sensitivities[1][1] - handledMatches[1][1]],
		['#ffab00', '#f5f5f5'],
		problemHandledDoughnutChartCtx
	));

	var warningHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_warning").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		avoidZero(handledMatches[2][1], sensitivities[2][1]),
		// Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100.
		// This is so that the secondary color will fill the whole graph
		// this could be prettier, if we 'pre-calculated' the %
		[handledMatches[2][1], ((!sensitivities[2][1]) && (!handledMatches[2][1])) ? 100 : sensitivities[2][1] - handledMatches[2][1]],
		['#fed149', '#f5f5f5'],
		warningHandledDoughnutChartCtx
	));

	var notificationHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_notification").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		avoidZero(handledMatches[3][1], sensitivities[3][1]),
		// Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100.
		// This is so that the secondary color will fill the whole graph
		// this could be prettier, if we 'pre-calculated' the %
		[handledMatches[3][1], ((!sensitivities[3][1]) && (!handledMatches[3][1])) ? 100 : sensitivities[3][1] - handledMatches[3][1]],
		['#21759c', '#f5f5f5'],
		notificationHandledDoughnutChartCtx
	));

	var totalHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_total").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		isNaN(handledPercentage) ? 0 : handledPercentage.toFixed(0) + '%',
		[totalHandledMatches, (totalMatches - totalHandledMatches)],
		['#21759c', '#f5f5f5'],
		totalHandledDoughnutChartCtx
	));

}