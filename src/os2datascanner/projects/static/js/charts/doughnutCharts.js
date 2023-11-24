/* exported drawDoughnut */

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
			layout: {
				padding: {
				  left: 8,
				  right: 8,
				  top: 8,
				  bottom: 8
				}
			  },
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

function drawDoughnut(totalHandledMatches, totalMatches, handledPercentage) {
	// Doughnut chart
	// //
	// //
	// //
	// //
	// //
	// function for moving label to center of chart
	Chart.register({
		id: "chartID",
		beforeDraw: function (chart) {
			if (chart.config.type === 'doughnut') {
				var ctx, centerConfig, fontStyle, txt, weight, color, maxFontSize, sidePadding, sidePaddingCalculated;
				if (chart.config.options.elements.center) {
					// Get ctx from string
					ctx = chart.ctx;

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

	// function for rounded corners
	Chart.register({
		id: "chartID",
		afterUpdate: function (chart) {
			if (chart.config.options.elements.arc.roundedCornersFor !== undefined) {
				var arc = chart.getDatasetMeta(0).data[chart.config.options.elements.arc.roundedCornersFor];
				arc.round = {
					x: (chart.chartArea.left + chart.chartArea.right) / 2,
					y: (chart.chartArea.top + chart.chartArea.bottom) / 2,
					radius: (chart.outerRadius + chart.innerRadius) / 2,
					thickness: (chart.outerRadius - chart.innerRadius) / 2 - 1,
					backgroundColor: arc.backgroundColor
				};
			}
		},

		afterDraw: function (chart) {
			if (chart.config.options.elements.arc.roundedCornersFor !== undefined) {
				var ctx = chart.ctx;
				var arc = chart.getDatasetMeta(0).data[chart.config.options.elements.arc.roundedCornersFor];
				var startAngle = Math.PI / 2 - arc.startAngle;
				var endAngle = Math.PI / 2 - arc.endAngle;

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

	var totalHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_total").getContext('2d');
	charts.push(makeDoughnutChart(
		// logic to avoid 0 divided by 0 being NaN
		isNaN(handledPercentage) ? 0 : handledPercentage.toFixed(0) + '%',
		[totalHandledMatches, (totalMatches - totalHandledMatches)],
		['#21759c', '#f5f5f5'],
		totalHandledDoughnutChartCtx
	));

}