
function getDigitLength(number) {
  return number.toString().length;
}

function bytesToKB(bytes) {
  if (bytes === 0) {return 0;}
  let KB = parseInt((bytes / Math.pow(1024, 1)).toFixed(1));
  return KB;
}

function binAndCount(array, binVal){
  // divides array into bins with a range of approx {binVal} % of total range
  // counts number of instances in each bin

  let max = Math.max.apply(Math, array);
  let binSize = Math.round(max*(binVal/100));
  let roundNumber = Math.pow(10, getDigitLength(binSize)-1);
  binSize = Math.round(binSize/roundNumber)*roundNumber;
  let nBins = Math.ceil(max/binSize);
  if (Number.isInteger(max/binSize)){
    nBins++;
  }

  let counts = Array(nBins).fill(0);
  for (let i = 0; i < array.length; i++ ){
    let index = Math.floor(array[i]/binSize);
    counts[index]++;
  }
  return [counts, binSize];
}

function getData(dataArray, granularity=5){ // jshint ignore:line
  // bins and counts dataArray
  // begins with a binrange of approx {granularity} % of total range
  // balances number of vary large and very small bins
  // balancing values are rather arbitrary - should they be soft-coded???
  // binsize is passed as it is used to create appropriate labels for tooltips

  dataArray.sort(function(a,b) {
    return a-b;
  });

  const converted = dataArray.map(byte => bytesToKB(byte));
  var [counts, binSize] = binAndCount(converted, granularity);
  var nLarge = counts.filter((val)=>val>converted.length*0.05).length;
  var nSmall = counts.filter((val)=>val<=0).length;

  // If there are too many bins with much data in it, make granularity finer
  let i=0.5;
  while (nLarge > 7) {
    [counts, binSize] = binAndCount(converted, granularity-i);
    nLarge = counts.filter((value)=>value>converted.length*0.05).length;
    i+=0.5;
  }

  // If there are too many bins with zero or one datapoint, make granularity more coarse
  let j = 0.5;
  while (nSmall/counts.length > 0.3){
    [counts, binSize] = binAndCount(converted, granularity+j);
    nSmall = counts.filter((val)=>val ===0).length;
    j+=0.5;
  }

  let nBins = counts.length;
  let labels = [];
  for (let i = 0; i<nBins; i++){
    labels.push(binSize*i+(binSize/2));
  }
  let points = labels.map((c, i) => ({x: c, y: counts[i]}));
  return [points, binSize];
}

function createBars(data, ctx, titleText, binSize){ // jshint ignore:line
  const bar = new Chart(ctx, {
    type: 'bar',
    data: {
      datasets: [{
        data: data,
        backgroundColor: "rgba(100, 44, 145, 0.8)",
        barPercentage: 1, 
        categoryPercentage: 1
      }]
    },
    options: {
      scales: {
        x: {
            type: 'linear',
            offset: false,
            grid: {
              offset: false
            },
            ticks: {
              stepSize: binSize,
              color: 'black',
              font: {
                size: 13
              }
            },
            title: {
              display: true,
              text: 'KB',
              font: {
                  size: 16
              },
              color: 'black'
            }
        }, 
        y: {
            beginAtZero: true,
            title: {
              display: true,
              text: gettext('Number of files'),
              font: {
                  size: 16
              },
              color: 'black'
            },
            ticks: {
              color: 'black',
              font: {
                size: 14
              }
            }
        }
      },
      plugins: {
        legend: {
        display: false
        },
        title: {
          display: true,
          text: titleText,
          font: {
            size: 20,
          },
          color: "black",
          align: "center"
        },
        scales: {
          xAxes: [{
            ticks: {
              fontSize: 12,
              weight: 'bold'}
          }]
        },
        datalabels: {
          display: false
        },
        tooltip: {
          backgroundColor: 'white',
          borderColor: "rgba(100, 44, 145, 0.8)",
          borderWidth: 1,
          titleColor: 'black',
          titleAlign: 'center',
          bodyColor: 'black',
          displayColors: false,
          padding: 10,
          callbacks: {
            label:(tooltipItem)=>{
              let start = parseInt(tooltipItem.label) - (binSize/2);
              let end = parseInt(tooltipItem.label) + (binSize/2);
                return `${start}-${end} KB`;},
            title:(tooltipItem) =>{
              let val = tooltipItem[0].formattedValue;
              if (val === '1'){
                return val.toString().concat(" ", gettext("file"));
              }
              else {
                return val.toString().concat(" ", gettext("files"));
              }
            }
          }
        }
      }
        
    },
    maintainAspectRatio: false,
    responsive: true,
  });
  return bar;
}

