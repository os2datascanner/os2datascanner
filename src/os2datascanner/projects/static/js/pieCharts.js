/* exported drawPies */

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

function drawPies(sourceTypes, handledMatchesStatus) {
  // Pie Chart start
  //
  //
  //
  //
  //
  // Creating datasources pie chart
  var dataSourcesPieChartCtx = document.querySelector("#pie_chart_datasources").getContext('2d');

  var dataSourcesPieChart = makePieChart(
    getDatasetLabels(sourceTypes, 0, 1),
    getDatasetData(sourceTypes, 1),
    colorData(sourceTypes, 1, ['#fed149', '#5ca4cd', '#21759c', '#00496e']),
    dataSourcesPieChartCtx
  );

  charts.push(dataSourcesPieChart);

  $("#pie_legend_datasources").html(unorderedListLegend(dataSourcesPieChart));

  var datasourcesLegendItems = document.querySelector("#pie_legend_datasources").getElementsByTagName('li');
  for (var j = 0; j < datasourcesLegendItems.length; j += 1) {
    datasourcesLegendItems[j].addEventListener("click", pieChartLegendClickCallback, false);
  }

  // Creating resolution_status pie chart
  var resolutionStatusPieChartCtx = document.querySelector("#pie_chart_resolution_status").getContext('2d');

  // sort the handledMatchesStatus the way we like it!
  handledMatchesStatus = [3, 2, 1, 4, 0].map(i => handledMatchesStatus[i]);

  var resolutionStatusPieChart = makePieChart(
    getDatasetLabels(handledMatchesStatus, 1, 2),
    getDatasetData(handledMatchesStatus, 2),
    colorData(handledMatchesStatus, 2, ['#80ab82', '#a2e774', '#35bd57', '#1b512d', '#7e4672']),
    resolutionStatusPieChartCtx
  );

  charts.push(resolutionStatusPieChart);

  $("#pie_legend_resolution_status").html(unorderedListLegend(resolutionStatusPieChart));

  var resolutionStatusLegendItems = document.querySelector("#pie_legend_resolution_status").getElementsByTagName('li');
  for (var k = 0; k < resolutionStatusLegendItems.length; k += 1) {
    resolutionStatusLegendItems[k].addEventListener("click", pieChartLegendClickCallback, false);
  }

  function pieChartLegendClickCallback(event) {
    event = event || window.event;

    var target = event.target || event.srcElement;

    while (target.nodeName !== 'LI') {
      target = target.parentElement;
    }

    var parent = target.parentElement;
    var chartId = parseInt(parent.id);
    var chart = Chart.instances[chartId];
    var index = Array.prototype.slice.call(parent.children).indexOf(target);
    var meta = chart.getDatasetMeta(0);
    var item = meta.data[index];

    chart.options.animation.duration = 400;
    // Run chart.update() to "reset" the chart and then add outerRadius after.
    chart.update();
    item._model.outerRadius += 5;
  }

  function colorData(dataset, dataIndex, colorList) {
    return findRelevantData(dataset, dataIndex).map(i => colorList[i]);
  }

  function getDatasetLabels(dataset, labelIndex, dataIndex) {
    let relevantIndices = findRelevantData(dataset, dataIndex);
    let relevantLabels = [];
    for (let index of relevantIndices) {
      relevantLabels.push(dataset[index][labelIndex]);
    }
    return relevantLabels;
  }

  function getDatasetData(dataset, dataIndex) {
    let relevantIndices = findRelevantData(dataset, dataIndex);
    let relevantData = [];
    for (let index of relevantIndices) {
      relevantData.push(dataset[index][dataIndex]);
    }
    return relevantData;
  }

  function findRelevantData(dataset, dataIndex) {
    let relevantIndices = [];
    for (let i = 0; i < dataset.length; i++) {
      if (dataset[i][dataIndex] > 0) {
        relevantIndices.push(i);
      }
    }
    return relevantIndices;
  }
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