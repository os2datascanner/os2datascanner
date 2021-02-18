// Color function
// reads colors from :root 
const colorFunction = function (color) {
  return getComputedStyle(document.querySelector(':root')).getPropertyValue(color);
}

// Set default animation duration on charts - this can be changed for each chart if needed.
Chart.defaults.global.animation.easing = 'easeOutQuad';
Chart.defaults.global.animation.duration = 1700;


// // Bar Chart start
// // 
// // 
// // 
// // 
// // 
// Function for creating gradient background for each bar size.
Chart.pluginService.register({
  afterUpdate: function(chart) {
      if (chart.config.type === 'bar'){
    
      // For every dataset ...
      for (var i = 0; i < chart.config.data.datasets.length; i++) {
        // We store it
        var dsMeta = chart.getDatasetMeta(i) 
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
            
            // The colors of the gradient that were defined in the data
            // gradient.addColorStop(0, dataset.backgroundColor[j][0]);
            // gradient.addColorStop(1, dataset.backgroundColor[j][1]);

            //Use this instead of ^ if we need the same color every time
            gradient.addColorStop(0, dataset.backgroundColor[0][0]);
            gradient.addColorStop(1, dataset.backgroundColor[0][1]);

              // We set this new color to the data background

              model.backgroundColor = gradient;
          }
      }
  }}
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
  if (typeof cornerRadius == 'undefined') {
    cornerRadius = 0;
  }
  if (typeof fullCornerRadius == 'undefined') {
    fullCornerRadius = false;
  }
  if (typeof stackedRounded == 'undefined') {
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
    if (nextCornerId == 4) {
      nextCornerId = 0
    }

    nextCorner = cornerAt(nextCornerId);

    width = corners[2][0] - corners[1][0];
    height = corners[0][1] - corners[1][1];
    x = corners[1][0];
    y = corners[1][1];

    var radius = cornerRadius;
    // Fix radius being too large
    if (radius > Math.abs(height) / 2) {
      radius = Math.floor(Math.abs(height) / 2);
    }
    if (radius > Math.abs(width) / 2) {
      radius = Math.floor(Math.abs(width) / 2);
    }

    var x_tl, x_tr, y_tl, y_tr, x_bl, x_br, y_bl, y_br;
    if (height < 0) {
      // Negative values in a standard bar chart
      x_tl = x;
      x_tr = x + width;
      y_tl = y + height;
      y_tr = y + height;

      x_bl = x;
      x_br = x + width;
      y_bl = y;
      y_br = y;

      // Draw
      ctx.moveTo(x_bl + radius, y_bl);

      ctx.lineTo(x_br - radius, y_br);

      // bottom right
      ctx.quadraticCurveTo(x_br, y_br, x_br, y_br - radius);


      ctx.lineTo(x_tr, y_tr + radius);

      // top right
      fullCornerRadius ? ctx.quadraticCurveTo(x_tr, y_tr, x_tr - radius, y_tr) : ctx.lineTo(x_tr, y_tr, x_tr - radius, y_tr);


      ctx.lineTo(x_tl + radius, y_tl);

      // top left
      fullCornerRadius ? ctx.quadraticCurveTo(x_tl, y_tl, x_tl, y_tl + radius) : ctx.lineTo(x_tl, y_tl, x_tl, y_tl + radius);


      ctx.lineTo(x_bl, y_bl - radius);

      //  bottom left
      ctx.quadraticCurveTo(x_bl, y_bl, x_bl + radius, y_bl);

    } else if (width < 0) {
      // Negative values in a horizontal bar chart
      x_tl = x + width;
      x_tr = x;
      y_tl = y;
      y_tr = y;

      x_bl = x + width;
      x_br = x;
      y_bl = y + height;
      y_br = y + height;

      // Draw
      ctx.moveTo(x_bl + radius, y_bl);

      ctx.lineTo(x_br - radius, y_br);

      //  Bottom right corner
      fullCornerRadius ? ctx.quadraticCurveTo(x_br, y_br, x_br, y_br - radius) : ctx.lineTo(x_br, y_br, x_br, y_br - radius);

      ctx.lineTo(x_tr, y_tr + radius);

      // top right Corner
      fullCornerRadius ? ctx.quadraticCurveTo(x_tr, y_tr, x_tr - radius, y_tr) : ctx.lineTo(x_tr, y_tr, x_tr - radius, y_tr);

      ctx.lineTo(x_tl + radius, y_tl);

      // top left corner
      ctx.quadraticCurveTo(x_tl, y_tl, x_tl, y_tl + radius);

      ctx.lineTo(x_bl, y_bl - radius);

      //  bttom left corner
      ctx.quadraticCurveTo(x_bl, y_bl, x_bl + radius, y_bl);

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
        if (fullCornerRadius || typeOfChart == 'horizontalBar')
          ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        else
          ctx.lineTo(x + width, y + height, x + width - radius, y + height);


        ctx.lineTo(x + radius, y + height);

        // bottom left
        if (fullCornerRadius)
          ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        else
          ctx.lineTo(x, y + height, x, y + height - radius);


        ctx.lineTo(x, y + radius);

        // top left
        if (fullCornerRadius || typeOfChart == 'bar')
          ctx.quadraticCurveTo(x, y, x + radius, y);
        else
          ctx.lineTo(x, y, x + radius, y);
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
Chart.pluginService.register({
  beforeDraw: function(chart) {
    if (typeof chart.config.options.lineAt != 'undefined') {
      var lineAt = chart.config.options.lineAt;
      var ctxPlugin = chart.chart.ctx;
      var xAxe = chart.scales[chart.config.options.scales.xAxes[0].id];
      var yAxe = chart.scales[chart.config.options.scales.yAxes[0].id];
      ctxPlugin.strokeStyle = colorFunction('--color-text-secondary');
      ctxPlugin.lineWidth = 2;
      ctxPlugin.setLineDash([5, 5])
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

// // array with testdata
// var values = unhandled;


// // sort array in descending order
// values.sort(function(a, b){return b[1]-a[1]});


// calculate the average
// this out-commented function works for double-indexed arrays with values at index[1]
// const unhandledMatchesAverage = unhandledMatches.reduce((sum, value) => sum + value[1], 0) / unhandledMatches.length;
// this function works for arrays with only values
const unhandledMatchesAverage = unhandledBarChartValues.reduce((a,b) => (a + b)) / unhandledBarChartValues.length;

new Chart(unhandledBarChartCtx, {
  type: 'bar',
  data: {
    labels: unhandledBarChartLabels,
    datasets: [{
      data: unhandledBarChartValues,
      backgroundColor: [
        [colorFunction('--color-primary-light'), colorFunction('--color-icon-primary')],
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
    // chartjs-plugin-datalabels.js
      datalabels: {
        display: false
      }
    },
    scales: {
      xAxes: [{
        gridLines: {
          display: false,
          // drawOnChartArea:false
        }
      }],
      yAxes: [{
        gridLines: {
            display: false,
            // drawOnChartArea:false
        },
        ticks: {
          beginAtZero: true,
          stepSize:50,
        }
      }]
    },
    lineAt: unhandledMatchesAverage, // Average line value
    responsive:true
  }
});

// Creating data for oldest matches

// var oldestBarChartCtx = document.querySelector("#bar_chart_oldest").getContext('2d');

// // Recieve data and create array for labels and data.

// var oldestBarChartLabels = [];
// var oldestBarChartValues = [];

// for(var i = 0; i<oldestMatches.length && i<5;i++) {
//   oldestBarChartLabels.push(oldestMatches[i][0]);
//   oldestBarChartValues.push(oldestMatches[i][1]);
// }

// // // array with testdata
// // var values = oldest;


// // // sort array in descending order
// // values.sort(function(a, b){return b[1]-a[1]});


// // calculate the average
// // this out-commented function works for double-indexed arrays with values at index[1]
// // const oldestMatchesAverage = oldestMatches.reduce((sum, value) => sum + value[1], 0) / oldestMatches.length;
// // this function works for arrays with only values
// const oldestMatchesAverage = oldestBarChartValues.reduce((a,b) => (a + b)) / oldestBarChartValues.length;

// new Chart(oldestBarChartCtx, {
//   type: 'bar',
//   data: {
//     labels: oldestBarChartLabels,
//     datasets: [{
//       data: oldestBarChartValues,
//       backgroundColor: [
//         [colorFunction('--color-primary-light'), colorFunction('--color-icon-primary')],
//       ],
//       barPercentage: 0.8,
//     }]
//   },
//   options: {
//     cornerRadius: 5, 
//     //Default: false; if true, this would round all corners of final box;
//     fullCornerRadius: true,
//     legend: {
//       display: false
//     },
//     tooltips: {
//       enabled: false
//     },
//     hover: {
//       mode: null
//     },
//     plugins: {
//     // chartjs-plugin-datalabels.js
//       datalabels: {
//         display: false
//       }
//     },
//     scales: {
//       xAxes: [{
//         gridLines: {
//           display: false,
//           // drawOnChartArea:false
//         }
//       }],
//       yAxes: [{
//         gridLines: {
//             display: false,
//             // drawOnChartArea:false
//         },
//         ticks: {
//           beginAtZero: true,
//           stepSize:10,
//           callback: function(label) {
//             return label+ ' dage';
//           }
//         }
//       }]
//     },
//     lineAt: oldestMatchesAverage, // Average line value
//     responsive:true
//   }
// });


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
    labels:[sensitivities[0][0],sensitivities[1][0],sensitivities[2][0],sensitivities[3][0]],
    datasets: [{
      data: [sensitivities[0][1],sensitivities[1][1],sensitivities[2][1],sensitivities[3][1]], 
      backgroundColor: colorarray = [colorFunction('--color-error'), colorFunction('--color-problem'), colorFunction('--color-warning'), colorFunction('--color-notification')],
      borderColor: colorarray,
      borderAlign: 'center',
      //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function 
      // (sensitivityLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
      hoverBorderWidth: [20,20,20,20]
    }]
  },
  options: {
    legend: {
      position:'top',
      align: 'end',
      display: false,
  
    },
    // Callback for placing legends inside of <ul>
    legendCallback: function(chart) {
      var text = [];
      text.push('<ul id="' + chart.id + '" class="pie_legend_list">');
      for (var i = 0; i < chart.data.datasets[0].data.length; i++) {
        text.push('<li><span id="bullet" style="color:' + chart.data.datasets[0].backgroundColor[i] + '">&#8226;</span>');
        if (chart.data.labels[i]) {
          text.push('<span>' + chart.data.labels[i]);
        }
        text.push('</span></li>');
      }
      text.push('</ul>');
      return text.join("");
    },
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
        posotion:'top',
        align:'end',
        formatter: (value, ctx) => {
          let sum = 0;
          let dataArr = ctx.chart.data.datasets[0].data;
          dataArr.map(data => {
            sum += data;
          });
          let percentage = (value*100 / sum).toFixed(0)+"%";
          return value ? percentage : '';
        },
        color: '#fff',
      }
    },
    responsive: true,
  }
});

$("#pie_legend_sensitivity").html(sensitivitiesPieChart.generateLegend());

var sensitivityLegendItems = document.querySelector("#pie_legend_sensitivity").getElementsByTagName('li');
for (var i = 0; i < sensitivityLegendItems.length; i += 1) {
  sensitivityLegendItems[i].addEventListener("click", sensitivityLegendClickCallback, false);
}

function sensitivityLegendClickCallback(event) {
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

// Creating datasources pie chart
var dataSourcesPieChartCtx = document.querySelector("#pie_chart_datasources").getContext('2d');

var dataSourcesPieChartLabels = [];
var dataSourcesPieChartValues = [];

for(var i = 0; i<dataSources.length && i<4;i++) {
  dataSourcesPieChartLabels.push(dataSources[i][0]);
  dataSourcesPieChartValues.push(dataSources[i][1]);
}

var dataSourcesPieChart = new Chart(dataSourcesPieChartCtx, {
  type: 'pie',
  data: {
    labels:dataSourcesPieChartLabels,
    datasets: [{
      data: dataSourcesPieChartValues, 
      backgroundColor: colorarray = [colorFunction('--color-warning'), colorFunction('--color-primary-light'), colorFunction('--color-notification'), colorFunction('--color-primary-dark')],
      borderColor: colorarray,
      borderAlign: 'center',
      //Put hoverBorderWidth on - this gives the canvas a small margin, so it doesn't 'cut off' when our 'click-highlight' function 
      // (datasourcesLegendClickCallback) is called. (the hover is not used, as the option: events is set to 0 ( events: [] ))
      hoverBorderWidth: [20,20,20,20]
    }]
  },
  options: {
    legend: {
      position:'top',
      align: 'end',
      display: false,
    },
    // Callback for placing legends inside of <ul>
    legendCallback: function(chart) {
      var text = [];
      text.push('<ul id="' + chart.id + '" class="pie_legend_list">');
      for (var i = 0; i < chart.data.datasets[0].data.length; i++) {
        text.push('<li><span id="bullet" style="color:' + chart.data.datasets[0].backgroundColor[i] + '">&#8226;</span>');
        if (chart.data.labels[i]) {
          text.push('<span>' + chart.data.labels[i]);
        }
        text.push('</span></li>');
      }
      text.push('</ul>');
      return text.join("");
    },
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
        posotion:'top',
        align:'end',
        formatter: (value, ctx) => {
          let sum = 0;
          let dataArr = ctx.chart.data.datasets[0].data;
          dataArr.map(data => {
            sum += data;
          });
          let percentage = (value*100 / sum).toFixed(0)+"%";
            
          return percentage ? percentage : null;
        },
        color: '#fff',
      }
    },
    responsive: true,
    // If we want the animation to start from the center - set to true
    // animation: {
    //     animateScale: true,
    // }
  }
});

$("#pie_legend_datasources").html(dataSourcesPieChart.generateLegend());

var datasourcesLegendItems = document.querySelector("#pie_legend_datasources").getElementsByTagName('li');
for (var i = 0; i < datasourcesLegendItems.length; i += 1) {
  datasourcesLegendItems[i].addEventListener("click", datasourcesLegendClickCallback, false);
}

function datasourcesLegendClickCallback(event) {
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
      }
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
  beforeDraw: function(chart) {
    if(chart.config.type == 'doughnut') {
      if (chart.config.options.elements.center) {
        // Get ctx from string
        var ctx = chart.chart.ctx;

        // Get options from the center object in options
        var centerConfig = chart.config.options.elements.center;
        var fontStyle = centerConfig.fontStyle || 'Arial';
        var txt = centerConfig.text;
        var weight = centerConfig.weight;
        var color = centerConfig.color || '#000';
        var maxFontSize = centerConfig.maxFontSize || 75;
        var sidePadding = centerConfig.sidePadding || 20;
        var sidePaddingCalculated = (sidePadding / 100) * (chart.innerRadius * 2)
        // Start with a base font of 30px
        ctx.font = weight +" 30px " + fontStyle;
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

      for (var n = 0; n < lines.length; n++) {
        ctx.fillText(lines[n], centerX, centerY);
        centerY += lineHeight;
      }
      //Draw text in center
      ctx.fillText(line, centerX, centerY);
    }
  }
});

var criticalHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_critical").getContext('2d');
new Chart(criticalHandledDoughnutChartCtx, {
  type: 'doughnut',
  data: {
    datasets: [{
      // Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100. 
      // This is so that the secondary color will fill the whole graph
      // this could be prettier, if we 'pre-calculated' the %
      data: [handledMatches[0][1], ((!sensitivities[0][1]) && (!handledMatches[0][1])) ? 100 : sensitivities[0][1]-handledMatches[0][1]],
      backgroundColor: [colorFunction('--color-error'), colorFunction('--color-hover')],
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
        // logic to avoid 0 divided by 0 being NaN
        text: isNaN(((handledMatches[0][1]/sensitivities[0][1])*100)) ? 0 + '%' : ((handledMatches[0][1]/sensitivities[0][1])*100).toFixed(0) + '%',
      }
    },
    plugins: {
      datalabels: {
        display: false
      },
    },
    events: [],
  } 
});

var problemHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_problem").getContext('2d');
new Chart(problemHandledDoughnutChartCtx, {
  type: 'doughnut',
  data: {
    datasets: [{
      // Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100. 
      // This is so that the secondary color will fill the whole graph
      // this could be prettier, if we 'pre-calculated' the %
      data: [handledMatches[1][1], ((!sensitivities[1][1]) && (!handledMatches[1][1])) ? 100 : sensitivities[1][1]-handledMatches[1][1]],
      backgroundColor: [colorFunction('--color-problem'), colorFunction('--color-hover')],
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
        // logic to avoid 0 divided by 0 being NaN
        text: isNaN(((handledMatches[1][1]/sensitivities[1][1])*100)) ? 0 + '%' : ((handledMatches[1][1]/sensitivities[1][1])*100).toFixed(0) + '%',
      }
    },
    plugins: {
      datalabels: {
        display: false
      },
    },
    events: [],
  } 
});

var warningHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_warning").getContext('2d');
new Chart(warningHandledDoughnutChartCtx, {
  type: 'doughnut',
  data: {
    datasets: [{
      // Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100. 
      // This is so that the secondary color will fill the whole graph
      // this could be prettier, if we 'pre-calculated' the %
      data: [handledMatches[2][1], ((!sensitivities[2][1]) && (!handledMatches[2][1])) ? 100 : sensitivities[2][1]-handledMatches[2][1]],
      backgroundColor: [colorFunction('--color-warning'), colorFunction('--color-hover')],
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
        // logic to avoid 0 divided by 0 being NaN
        text: isNaN(((handledMatches[2][1]/sensitivities[2][1])*100)) ? 0 + '%' : ((handledMatches[2][1]/sensitivities[2][1])*100).toFixed(0) + '%',
      }
    },
    plugins: {
      datalabels: {
        display: false
      },
    },
    events: [],
  } 
});

var notificationHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_notification").getContext('2d');
new Chart(notificationHandledDoughnutChartCtx, {
  type: 'doughnut',
  data: {
    datasets: [{
      // Terrible logic - makes sure that if both numbers are 0, 2nd number in the array will be 100. 
      // This is so that the secondary color will fill the whole graph
      // this could be prettier, if we 'pre-calculated' the %
      data: [handledMatches[3][1], ((!sensitivities[3][1]) && (!handledMatches[3][1])) ? 100 : sensitivities[3][1]-handledMatches[3][1]],
      backgroundColor: [colorFunction('--color-notification'), colorFunction('--color-hover')],
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
        text: isNaN((handledMatches[3][1]/sensitivities[3][1])*100) ? 0 + '%' : ((handledMatches[3][1]/sensitivities[3][1])*100).toFixed(0) + '%',
      }
    },
    plugins: {
      datalabels: {
        display: false
      },
    },
    events: [],
  } 
});
var totalHandledDoughnutChartCtx = document.querySelector("#doughnut_chart_total").getContext('2d');
new Chart(totalHandledDoughnutChartCtx, {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [totalHandledMatches, (totalMatches-totalHandledMatches)],
      backgroundColor: [colorFunction('--color-notification'), colorFunction('--color-hover')],
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
        text: isNaN(handledPercentage) ? 0 : handledPercentage.toFixed(0) + '%', 
      }
    },
    plugins: {
      datalabels: {
        display: false
      },
    },
    events: [],
  } 
});

// Line chart
// // 
// // 
// // 
// // 
// // 
// Creating xx line chart

// Chart.pluginService.register({
//   // This works to coor th backgournd
//   beforeDraw: function (chart, easing) {

//   if (chart.config.options.chartArea && chart.config.options.chartArea.backgroundColor) {
//     var ctx = chart.chart.ctx;
//     var chartArea = chart.chartArea;

//     var meta = chart.getDatasetMeta(0);

//     // half the width of a 'bar'
//     var margin = (meta.data[1]._model.x-meta.data[0]._model.x)/2;
    
//     // Position at index 2 - margin (index 0 is null) 
//     var start = meta.data[1]._model.x-margin;

//     var stop  = meta.data[meta.data.length-1]._model.x-margin;
    
//     ctx.save();
//     ctx.fillStyle = chart.config.options.chartArea.backgroundColor;

//     ctx.fillRect(start, chartArea.top, stop - start, chartArea.bottom - chartArea.top);
//     ctx.restore();
//     }
//   }
// });

// var lineChartData = {
//   labels: ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", ""],
//   datasets: [{
//     data: [ null, 5, 10, 18, 33, 121, 184, 179, 196, 158, 166, 66, 20, null],
//     fill: 0,
//     pointRadius: 0,
//     pointHitRadius: 20,
//     borderWidth: 4,
//     borderCapStyle: 'round',
//     tension: 0,
//     borderColor: '#21759C',
//     pointHoverRadius: 10,
//     hoverBackgroundColor: '#21759C',
//   }],
// }

// var lineChartOptions = {
//   tooltips: {
//     // Disable the on-canvas tooltip
//     enabled: false,

//     custom: function(tooltipModel) {
//       // Tooltip Element
//       var tooltipEl = document.getElementById('chartjs-tooltip');

//       // Create element on first render
//       if (!tooltipEl) {
//         tooltipEl = document.createElement('div');
//         tooltipEl.id = 'chartjs-tooltip';
//         tooltipEl.innerHTML = '<table></table>';
//         document.body.appendChild(tooltipEl);
//       }

//       // Hide if no tooltip
//       if (tooltipModel.opacity === 0) {
//         tooltipEl.style.opacity = 0;
//         return;
//       }

//       // Set caret Position
//       tooltipEl.classList.remove('above', 'below', 'no-transform');
//       if (tooltipModel.yAlign) {
//         tooltipEl.classList.add(tooltipModel.yAlign);
//       } else {
//         tooltipEl.classList.add('no-transform');
//       }

//       function getBody(bodyItem) {
//         return bodyItem.lines;
//       }

//       // Set Text
//       if (tooltipModel.body) {
//         var titleLines = tooltipModel.title || [];
//         var bodyLines = tooltipModel.body.map(getBody);

//         var innerHtml = '<thead>';

//         titleLines.forEach(function(title) {
//           innerHtml += '<tr><th>' + title + '</th></tr>';
//         });
//         innerHtml += '</thead><tbody>';

//         bodyLines.forEach(function(body, i) {
//           var colors = tooltipModel.labelColors[i];
//           var style = 'background:' + colors.backgroundColor;
//           style += '; border-color:' + colors.borderColor;
//           style += '; border-width: 2px';
//           var span = '<span style="' + style + '"></span>';
//           innerHtml += '<tr><td>' + span + body + '</td></tr>';
//         });
//         innerHtml += '</tbody>';

//         var tableRoot = tooltipEl.querySelector('table');
//         tableRoot.innerHTML = innerHtml;
//       }

//       // `this` will be the overall tooltip
//       var position = this._chart.canvas.getBoundingClientRect();

//       // Display, position, and set styles for font
//       tooltipEl.style.opacity = 1;
//       tooltipEl.style.position = 'absolute';
//       tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
//       tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
//       tooltipEl.style.fontFamily = tooltipModel._bodyFontFamily;
//       tooltipEl.style.fontSize = '1rem';
//       tooltipEl.style.fontStyle = tooltipModel._bodyFontStyle;
//       tooltipEl.style.padding = tooltipModel.yPadding + 'px ' + tooltipModel.xPadding + 'px';
//       tooltipEl.style.pointerEvents = 'none';
//       tooltipEl.style.borderRadius = '3px';
    
//       tooltipEl.style.backgroundColor = 'rgba(255,255,255, 0.8)';
//     }
//   },
//   legend: false,
//   responsive: true,
//   maintainAspectRatio: true,
//   elements: {
//     line: {
//       borderJoinStyle: 'round'
//     }
//   },
//   chartArea: {
//     backgroundColor: '#F5F5F5'
//   },
//   scales: {
//     color: '#FFF',
//     xAxes: [{
//       gridLines: {
//         offsetGridLines: true,
//         display: true,                
//         color: '#fff',
//         lineWidth: 3
//       },
//       ticks: {
//         fontSize: 16,
//       }
//     }],
//     yAxes: [{
//       gridLines: {
//         display: false
//       },
//       ticks: {
//         beginAtZero: true,
//         fontSize: 14,
//         stepSize:100,
//       }
//     }]
//   },
// }
// var ctx = document.querySelector("#chart").getContext('2d');
// new Chart(ctx, {
//   type: 'line',
//   data: lineChartData,
//   options: lineChartOptions
// });

// Select list
$('.dropdown').click(function () {
  $(this).attr('tabindex', 1).focus();
  $(this).toggleClass('active');
  $(this).find('.dropdown-menu').slideToggle(300);
});

$('.dropdown').focusout(function () {
    $(this).removeClass('active');
  $(this).find('.dropdown-menu').slideUp(300);
});
$('.dropdown .dropdown-menu li').click(function () {
  if($(this).text() != $(this).parents('.dropdown').find('.select_span').text()) {
    $(this).parents('.dropdown').find('span')[0].firstChild.data = $(this).text();
    // Was part of the solution - haven't found a use for it
    // $(this).parents('.dropdown').find('input').attr('value', $(this).attr('id'));
 
  }
});

// Toggle the class 'hidden' on change from the select list 

$(document).ready(function(){
  $(".select_span").on('DOMSubtreeModified',function(){
    $($(this).parents('.statistic').find('.chart_container, .chart_description').toggleClass("hidden"));
  });
});
