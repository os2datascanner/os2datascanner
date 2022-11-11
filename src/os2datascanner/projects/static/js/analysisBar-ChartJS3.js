// import jsonData from './magenta_data.json' assert {type: 'json'} // jshint ignore:line

const jsonData = [
    {"type": "image/png",
    "sizes": [3277, 3277, 5602, 6445, 6562, 7628, 7628, 8580, 8810, 9215, 9215, 9327, 9327, 9332, 9692, 9692, 10104, 10104, 10976, 10976, 11000, 11924, 11924, 15220, 16065, 16526, 18802, 19179, 19467, 19479, 19660, 20009, 20415, 20518, 22256, 23085, 23284, 23350, 23569, 23569, 23856, 23856, 23927, 23927, 25048, 25547, 25822, 26996, 28514, 29631, 30320, 34308, 34583, 35413, 35926, 37458, 38138, 38806, 39718, 40013, 40576, 40576, 42110, 42395, 43003, 45548, 46026, 46956, 47331, 47899, 48317, 49469, 50996, 53254, 56236, 58005, 58827, 61846, 62350, 62442, 62969, 67967, 72741, 77919, 80844, 82257, 84600, 84810, 86197, 87728, 94500, 99831, 103687, 103765, 107718, 108610, 110496, 110956, 114543, 118461, 119728, 127722, 131972, 135053, 140617, 141727, 153102, 163026, 191903, 203252, 205843, 235927, 246579, 267507, 274487, 462178, 463401, 463401, 464271, 487693, 529575, 598726, 631091, 687165, 715636]
    },
    {"type": "image/jpeg",
    "sizes": [12813, 13340, 20044, 20585, 22837, 29321, 29321, 30856, 31780, 31780, 32524, 33000, 33000, 33208, 34204, 35239, 36702, 37299, 38591, 38689, 40854, 43636, 43878, 44699, 44807, 46621, 49826, 52288, 52653, 53321, 55045, 56119, 56205, 58232, 59113, 59113, 61051, 65162, 65162, 66758, 66758, 67001, 67001, 67774, 67774, 67934, 69867, 73110, 74439, 74439, 74516, 74516, 75016, 75016, 77068, 78135, 78135, 78410, 78410, 78468, 78839, 78839, 80376, 80376, 82218, 82218, 82563, 82563, 83098, 84051, 84051, 84362, 84362, 86370, 86370, 86561, 86833, 86833, 87888, 87888, 88281, 88281, 88418, 88944, 88944, 89064, 89829, 89846, 89846, 89951, 89951, 91208, 91208, 92666, 92666, 93664, 93664, 93924, 93924, 94460, 94460, 96305, 96305, 96817, 96817, 97843, 97843, 98987, 99240, 99240, 100612, 101063, 101063, 101879, 101879, 102321, 102321, 103175, 103175, 103238, 103870, 103870, 104329, 104329, 104608, 104608, 105892, 105892, 105905, 105905, 106604, 106604, 108433, 108433, 108515, 108515, 109496, 109496, 111086, 111086, 115186, 115186, 117086, 117086, 117920, 117920, 118261, 118261, 119910, 119910, 120723, 120723, 120759, 120759, 124047, 125150, 125150, 126723, 126723, 129580, 129580, 131046, 131046, 133984, 133984, 135015, 138700, 138700, 138877, 138877, 142264, 142264, 143093, 144029, 144029, 150596, 151838, 153468, 153468, 163945, 166882, 166882, 166974, 175446, 175446, 177397, 214012, 216876, 216876, 236180, 248105, 248105, 259932, 259932, 265981, 267609, 267609, 291426, 309473, 309473, 310110, 310110, 333168, 333168, 340690, 340690, 352400, 378241, 378241, 383773, 383773, 385520, 385520, 393592, 397731, 397731, 422172, 422172, 422361, 422361, 447746, 447746, 457652, 457652, 459962, 459962, 461758, 461758, 464825, 464825, 470347, 470347, 473287, 473287, 476675, 476675, 480406, 480406, 482305, 482305, 498712, 498712, 502468, 502468, 506163, 506163, 510767, 510767, 514408, 514408, 535536, 535536, 540309, 540309, 541765, 541765, 557176, 557176, 559661, 559661, 564385, 564385, 575371, 575371, 589122, 596544, 596544, 635058, 635058]
    },
    {"type": "PDF",
    "sizes": [678423,83523,586045,393947,470404,412541, 736222, 652321, 530723, 194094, 211932, 714915, 375268, 412209, 189560, 704106, 94267, 596858, 689670, 708537, 741939, 751743, 679466, 274276, 356797, 124987, 435247, 696197, 132523, 769959, 80683, 694238, 221632, 637463, 423812, 135387, 754801, 168449, 654236, 373358, 419734, 418310, 539423, 80347, 145626, 738416, 405811, 717525, 755953, 571319, 218603, 337923, 511652, 660573, 417893, 678608, 570992, 112469, 310543, 289163, 491145, 439459, 429626, 589215, 364829, 701506, 129382, 230131, 781817, 688584, 610341, 429722, 595607, 627370, 732125, 88483, 651226, 237027, 679984, 250420, 673301, 740072, 503518, 473858, 274209, 633002, 717201, 293236, 731193, 191343, 190414, 390066, 399596, 629851, 269728, 494258, 128300, 706440, 138654, 106827, 85009, 726515, 293658, 519257, 386506, 643874, 502470, 732633, 700187, 140829, 552332, 303451, 455053, 632837, 277296, 676614, 88735, 585980, 201469, 201816, 552452, 289276, 237813, 121369, 580243, 265474, 644348, 444410, 289960, 626478, 588100, 439240, 147712, 201658, 284170, 605394, 334466, 721336, 677357, 428116, 120470, 210161, 727784, 243071, 587130, 113079, 558130, 347748, 698568, 681709, 657551, 528261, 698090, 127677, 535053, 732294, 290798, 575468, 309421, 225279, 200410, 513271, 799914, 351024, 452668, 558428, 738480, 550899, 349970, 245636, 561588, 613722, 232104, 507888, 137119, 247874, 82930, 531547, 640840, 395643, 741987, 286095, 185383, 178853, 512258, 771022, 355934, 752652, 316957, 196172, 171708, 603308, 676511, 683015, 156704, 238029, 268399, 386164, 350131, 338384, 141623, 727474, 111895, 505291, 393756, 196480, 253506, 681229, 225092, 718972, 358324, 93686, 729113, 671979, 445251, 95075, 94432, 415516, 280359, 132160, 242628, 667091, 187527, 322249, 322050, 536953, 796713, 321164, 406627, 321593, 474696, 442861, 795418, 416403, 58532, 363174, 230285, 192252, 368530, 641852, 164759, 737102, 272493, 227442, 93927, 510992, 167984, 542897, 592857, 701837]
    }
];

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

function getData(dataArray, granularity=5){
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

function drawBars(jsonData){
  jsonData.forEach((dataset, i) => {
    let ctx = document.getElementById("bar"+(i+1).toString());
    let [data, binSize] = getData(dataset.sizes);
    let title = dataset.type.charAt(0).toUpperCase() + dataset.type.slice(1);
    createBars(data, ctx, title, binSize);
  });
}

function createBars(data, ctx, titleText, binSize){
  new Chart(ctx, {
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
              text: 'Number of files',
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
                return `${val} file`;
              }
              else {
                return `${val} files`;
              }
            }
          }
        }
      }
        
    },
    maintainAspectRatio: false,
    responsive: true,
  });
  
}

drawBars(jsonData);