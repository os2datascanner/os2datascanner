// Color function
// reads colors from :root 
const colorFunction = function (color) {
  return getComputedStyle(document.querySelector(':root')).getPropertyValue(color);
}

  // // 
  // // Bar Chart start
  // // 
  // // 
  // // 
  // // 
  // // 

  var sens = [['Kritisk',8],['Problem',12],['Advarsel',30],['Notifikation',50]];
  var unhandled = [['David',30],['Sofie',20],['Anders',10],['Else',17]];
  
  
  // function for rounded corners
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
              gradient = barCtx.createLinearGradient(0, start, 0, end);
              
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
  
  Chart.elements.Rectangle.prototype.draw = function() {
      var ctx = this._chart.ctx;
      var vm = this._view;
      var left, right, top, bottom, signX, signY, borderSkipped, radius;
      var borderWidth = vm.borderWidth;
    
      // If radius is less than 0 or is large enough to cause drawing errors a max
      //      radius is imposed. If cornerRadius is not defined set it to 0.
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
              ctxPlugin.strokeStyle = "#777777";
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
  
  var barCtx = document.querySelector("#bar_chart_unhandled").getContext('2d');
  
  // array with testdata
  var values = unhandled;

  
  // sort array in descending order
  values.sort(function(a, b){return b[1]-a[1]});
  

  // calculate the average
  var average = values.reduce((sum, value) => sum + value[1], 0) / values.length;


  var barChartData = {
    labels: [values[0][0],values[1][0],values[2][0],values[3][0]],
    datasets: [{
      data: [values[0][1],values[1][1],values[2][1],values[3][1]],
        backgroundColor: [
          [colorFunction('--color-primary-light'), colorFunction('--color-icon-primary')],
        ],
      barPercentage: 0.8,
    }]
  }
  var barChartOptions = {
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
                stepSize:10,
                callback: function(label) {
                  return label+ ' dage';
                }
            }
          }]
      },
      lineAt: average, // Average line value
      responsive:true
  }
  
  new Chart(barCtx, {
      type: 'bar',
      data: barChartData,
      options: barChartOptions
  });

// 
// Pie Chart start
// 
// 
// 
// 
// 

var pieCtx = document.querySelector("#pie_chart_sensitivity").getContext('2d');

var pieChartData = {
    labels:[sens[0][0],sens[1][0],sens[2][0],sens[3][0]],
    datasets: [{
        data: [sens[0][1],sens[1][1],sens[2][1],sens[3][1]], 
        backgroundColor: colorarray = [colorFunction('--color-error'), colorFunction('--color-problem'), colorFunction('--color-warning'), colorFunction('--color-notification')],
        borderColor: colorarray,
        borderAlign: 'center'
    }]
}
var pieChartOptions = {
  legend: {
    position:'top',
    align: 'end',
    display: false,

  },
  // Callback for placing legends inside of <ul>
  legendCallback: function(chart) {
    var text = [];
    text.push('<ul class="pie_legend_list">');
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
        return percentage;
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

var myChart = new Chart(pieCtx, {
  type: 'pie',
  data: pieChartData,
  options: pieChartOptions
});

$("#pie_legend_sensitivity").html(myChart.generateLegend());


// Doughnut chart

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

var ctx1 = document.querySelector("#doughnut_chart_critical").getContext('2d');
var ctx2 = document.querySelector("#doughnut_chart_problem").getContext('2d');
var ctx3 = document.querySelector("#doughnut_chart_warning").getContext('2d');
var ctx4 = document.querySelector("#doughnut_chart_notification").getContext('2d');

new Chart(ctx1, {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [sens[0][1], (100-sens[0][1])],
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
            text: sens[0][1] +'%',
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
new Chart(ctx2, {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [sens[1][1], (100-sens[1][1])],
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
        text: sens[1][1] +'%',
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
new Chart(ctx3, {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [sens[2][1], (100-sens[2][1])],
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
        text: sens[2][1] +'%',
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
new Chart(ctx4, {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [sens[3][1], (100-sens[3][1])],
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
        text: sens[3][1] +'%',
        
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
