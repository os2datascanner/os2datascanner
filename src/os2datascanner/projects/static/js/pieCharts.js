/* exported drawPie */

function makePieChart(labels, data, colors, chartElement) {

  const pieChart = new Chart(chartElement, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 0,
        borderAlign: 'center',
        //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function
        // (sensitivityLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
        hoverBorderWidth: 20
      }]

    },
    options: {
      events: [],
      plugins: {
        // Fomat label to be shown as "x%"
        datalabels: {
          font: {
            size: 16,
            weight: 'bold'
          },
          position: 'top',
          align: 'center',
          formatter: function (value, ctx) {
            let dataArr = ctx.chart.data.datasets[0].data;
            let sum = dataArr.reduce(function (total, frac) { return total + frac; });
            var percentage = Math.round(value * 100 / sum) + "%";
            return value ? percentage : '';
          },
          color: '#fff',
        },
        legend: {
          position: 'top',
          align: 'end',
          display: false,
        },
        tooltip: {
          enabled: true
        },
      },
      responsive: true,
      aspectRatio: 1,
      maintainAspectRatio: false
    },
    plugins: [ChartDataLabels]
  });

  return pieChart;
}

function drawPie(data, ctxName, colors) {
  const pieChartCtx = document.querySelector("#pie_chart_" + ctxName).getContext('2d');

  const pieChart = makePieChart(Object.values(data).map(obj => obj.label), Object.values(data).map(obj => obj.count), colors, pieChartCtx);

  charts.push(pieChart);

  $("#pie_legend_" + ctxName).html(unorderedListLegend(pieChart));
}

function unorderedListLegend(chart) {
  var text = [];
  text.push('<ul id="' + chart.id + '" class="pie_legend_list">');
  for (var i = 0; i < chart.data.datasets[0].data.length; i++) {
    text.push('<li><span class="bullet" style="color:' + chart.data.datasets[0].backgroundColor[i] + '">&#8226;</span>');
    if (chart.data.labels[i]) {
      text.push('<span>' + chart.data.labels[i]);
    }
    text.push('</span></li>');
  }
  text.push('</ul>');
  return text.join("");
}