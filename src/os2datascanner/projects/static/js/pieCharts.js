/* exported drawPies */

function drawPies(sensitivities, sourceTypes, handledMatchesStatus) {
  //
  // Pie Chart start
  //
  //
  //
  //
  //
  // Creating sensitivites pie chart

  var sensitivitiesPieChartCtx = document.querySelector("#pie_chart_sensitivity").getContext('2d');

  var sensitivitiesPieChart = new Chart(sensitivitiesPieChartCtx, {
    type: 'pie',
    data: {
      labels: [sensitivities[0][0], sensitivities[1][0], sensitivities[2][0], sensitivities[3][0]],
      datasets: [{
        data: [sensitivities[0][1], sensitivities[1][1], sensitivities[2][1], sensitivities[3][1]],
        backgroundColor: ['#e24e4e', '#ffab00', '#fed149', '#21759c'],
        borderColor: ['#e24e4e', '#ffab00', '#fed149', '#21759c'],
        borderAlign: 'center',
        //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function
        // (sensitivityLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
        hoverBorderWidth: [20, 20, 20, 20]
      }]

    },
    options: {
      legend: {
        position: 'top',
        align: 'end',
        display: false,

      },
      // Callback for placing legends inside of <ul>
      legendCallback: unorderedListLegend,
      tooltips: {
        enabled: false,
      },
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
          formatter: displayAsPercentage,
          color: '#fff',
        }
      },
      responsive: true,
      aspectRatio: 1,
      maintainAspectRatio: false
    }
  });

  charts.push(sensitivitiesPieChart);

  $("#pie_legend_sensitivity").html(sensitivitiesPieChart.generateLegend());

  var sensitivityLegendItems = document.querySelector("#pie_legend_sensitivity").getElementsByTagName('li');
  for (var i = 0; i < sensitivityLegendItems.length; i += 1) {
    sensitivityLegendItems[i].addEventListener("click", pieChartLegendClickCallback, false);
  }

  // Creating datasources pie chart
  var dataSourcesPieChartCtx = document.querySelector("#pie_chart_datasources").getContext('2d');

  var dataSourcesPieChart = new Chart(dataSourcesPieChartCtx, {
    type: 'pie',
    data: {
      labels: [sourceTypes[0][0], sourceTypes[1][0], sourceTypes[2][0], sourceTypes[3][0]],
      datasets: [{
        data: [sourceTypes[0][1], sourceTypes[1][1], sourceTypes[2][1], sourceTypes[3][1]],
        backgroundColor: ['#fed149', '#5ca4cd', '#21759c', '#00496e'],
        borderColor: ['#fed149', '#5ca4cd', '#21759c', '#00496e'],
        borderAlign: 'center',
        //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function
        // (sensitivityLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
        hoverBorderWidth: [20, 20, 20, 20]
      }]
    },
    options: {
      legend: {
        position: 'top',
        align: 'end',
        display: false,
      },
      // Callback for placing legends inside of <ul>
      legendCallback: unorderedListLegend,
      tooltips: {
        enabled: false,
      },
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
          formatter: displayAsPercentage,
          color: '#fff',
        }
      },
      responsive: true,
      aspectRatio: 1,
      maintainAspectRatio: false
      // If we want the animation to start from the center - set to true
      // animation: {
      //     animateScale: true,
      // }
    }
  });

  charts.push(dataSourcesPieChart);

  $("#pie_legend_datasources").html(dataSourcesPieChart.generateLegend());

  var datasourcesLegendItems = document.querySelector("#pie_legend_datasources").getElementsByTagName('li');
  for (var j = 0; j < datasourcesLegendItems.length; j += 1) {
    datasourcesLegendItems[j].addEventListener("click", pieChartLegendClickCallback, false);
  }

  // Creating resolution_status pie chart
  var resolutionStatusPieChartCtx = document.querySelector("#pie_chart_resolution_status").getContext('2d');

  var resolutionStatusPieChart = new Chart(resolutionStatusPieChartCtx, {
    type: 'pie',
    data: {
      labels: [handledMatchesStatus[3][1], handledMatchesStatus[2][1], handledMatchesStatus[1][1], handledMatchesStatus[4][1], handledMatchesStatus[0][1]],
      datasets: [{
        data: [handledMatchesStatus[3][2], handledMatchesStatus[2][2], handledMatchesStatus[1][2], handledMatchesStatus[4][2], handledMatchesStatus[0][2]],
        backgroundColor: ['#80ab82', '#a2e774', '#35bd57', '#1b512d', '#7e4672'],
        borderColor: ['#80ab82', '#a2e774', '#35bd57', '#1b512d', '#7e4672'],
        borderAlign: 'center',
        //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function
        // (sensitivityLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
        hoverBorderWidth: [20, 20, 20, 20, 20]
      }]
    },
    options: {
      legend: {
        position: 'top',
        align: 'end',
        display: false,
      },
      // Callback for placing legends inside of <ul>
      legendCallback: unorderedListLegend,
      tooltips: {
        enabled: false,
      },
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
          formatter: displayAsPercentage,
          color: '#fff',
        }
      },
      responsive: true,
      aspectRatio: 1,
      maintainAspectRatio: false
      // If we want the animation to start from the center - set to true
      // animation: {
      //     animateScale: true,
      // }
    }
  });

  charts.push(resolutionStatusPieChart);

  $("#pie_legend_resolution_status").html(resolutionStatusPieChart.generateLegend());

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

  function displayAsPercentage(value, ctx) {
    let dataArr = ctx.chart.data.datasets[0].data;
    let sum = dataArr.reduce(function (total, frac) { return total + frac; });
    var percentage = Math.round(value * 100 / sum) + "%";
    return value ? percentage : '';
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
}
