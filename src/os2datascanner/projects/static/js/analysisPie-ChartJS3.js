const Data = [
    {
        "type": "Image/png",
        "n_files":69, 
        "total_size":9720239, 
        "mean":140873, 
        "median":21267, 
        "min":736, 
        "max":1832836,
    },
    {
        "type":"Image/jpeg",
        "n_files":118, 
        "total_size":45597233, 
        "mean":386417, 
        "median":169746, 
        "min":2845, 
        "max":9355552,
    },
    {
        "type":"PDF",
        "n_files":82, 
        "total_size":10765558, 
        "mean":131287, 
        "median":120333, 
        "min":5362, 
        "max":264511,
    },
    {
        "type":"XLS",
        "n_files":105, 
        "total_size":31064800, 
        "mean":295855, 
        "median":118202, 
        "min":1213, 
        "max":212369,
    },
    {
        "type":"TXT",
        "n_files":135, 
        "total_size":12161999, 
        "mean":90088, 
        "median":92354, 
        "min":11234, 
        "max":150364,
    }
];


function displayAsPercentage(value, ctx) {
    let dataArr = ctx.chart.data.datasets[0].data;
    let sum = dataArr.reduce(function (total, frac) { return total + frac; });
    var percentage = Math.round(value * 100 / sum) + "%";
    return value ? percentage : '';
}
  
  
function displayLabelUnit(index, chartObject) {
let dataset = chartObject.datasets[0];
let labelName = chartObject.labels[index];
if (dataset.name === "nfiles"){
    return `${labelName}: ${formatNumber(dataset.data[index])} files`;
}
else if (dataset.name === "storage"){
    return `${labelName}: ${bytesToSize(dataset.data[index])}`;
}
else {
    return `${labelName}: ${formatNumber(dataset.data[index])}`;
}
}

function bytesToSize(bytes) {
var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
if (bytes === 0) {return 'n/a';}
var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
if (i === 0) {return `${bytes} ${sizes[i]}`;}
return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

function formatNumber(x) {
return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function createPie(data, htmlElements, colors){
    let [ctx, pieCanvasID] = htmlElements;
    while (colors.length < data.labels.length){
        colors = colors.concat(colors);
    }
    let pie = new Chart(ctx, {
        type: "pie",
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: colors.slice(0, data.labels.length),
                borderColor: colors.slice(0, data.labels.length),
                borderAlign: "center",
                name: data.name
            }],
        },
        plugins: [
        ChartDataLabels,
        {
            beforeInit: function(chart) {
            if (chart.canvas.id === pieCanvasID) {
            const ul = document.createElement('ul');
            ul.setAttribute('class', 'chart-legend');
            for (let i=0; i<chart.data.labels.length; i++){
                ul.innerHTML += `
                <li>
                <span class="bullet" style="color:${chart.data.datasets[0].backgroundColor[i]}">&#8226;</span>
                </span>
                ${ displayLabelUnit(i, chart.data) }
                </li>
                `;
                }
            return document.getElementById(pieCanvasID+"_legend").appendChild(ul);
            }
            return;
            }
        },
        ],
        options: {
            plugins: {
            datalabels: {
                font: {
                size: 16,
                family: 'Arial'
                },
                position: 'top',
                align: 'end',
                offset: 1.2,
                formatter: displayAsPercentage,
                color: '#fff',
            },
            legend: {
                display:false,
                position: 'right',
                labels: {
                boxWidth: 7,
                boxHeight: 7,
                usePointStyle: true,
                font: {
                    size: 16
                },
                }
            },
            title: {
                display: true,
                text: data.title,
                font: {
                    size: 20,
                },
                color: "black",
                align: "center"
                },
            tooltip: {
                backgroundColor: 'white',
                borderWidth: 1,
                titleAlign: 'center',
                bodyColor: 'black',
                displayColors: false,
                callbacks: {
                    label:(tooltipItem)=>{
                        const name = tooltipItem.dataset.name;
                        const val = tooltipItem.raw;
                        const label = tooltipItem.label;
                        if (name === "storage"){
                            return `${label}: ${bytesToSize(val)}`;
                        }
                        else if (name === "nfiles"){
                            if (val === 1){
                                return `${label}: ${val} file`;
                            }   
                            else {
                                return `${label}: ${val} files`;
                            }
                        }
                        
                    //   let start = parseInt(tooltipItem.label) - (binSize/2);
                    //   let end = parseInt(tooltipItem.label) + (binSize/2);
                    //     return `${start}-${end} KB`;},
                    // title:(tooltipItem) =>{
                    //   let val = tooltipItem[0].formattedValue;
                    //   if (val === '1'){
                    //     return `${val} file`;
                    //   }
                    //   else {
                    //     return `${val} files`;
                    //   }
                    }
                  }
            },
            },
        responsive: true,
        aspectRatio: 1,
        maintainAspectRatio: false,
        }
    });
    return pie;
}

function drawPies(Data, colors) {
var ctx1 = document.getElementById("pie1");
var ctx2 = document.getElementById("pie2");
let types = Data.map(object => object.type);
let nFiles = Data.map(object => object.n_files); // jshint ignore:line
let totalSize = Data.map(object => object.total_size); // jshint ignore:line
let pie1Data = {labels: types, data: nFiles, name: "nfiles", title: "Number of files"};
let pie2Data = {labels: types, data: totalSize, name: "storage", title: "Storage space"};
createPie(pie1Data, [ctx1, "pie1"], colors);
createPie(pie2Data, [ctx2, "pie2"], colors);

}



let colorList = ["rgba(84, 71, 140)", 
                "rgba(44, 105, 154)",
                "rgba(4, 139, 168)",
                "rgba(13, 179, 158)",
                "rgba(22, 219, 147)",
                "rgba(131, 227, 119)",
                "rgba(185, 231, 105)",
                "rgba(239, 234, 90)",
                "rgba(241, 196, 83)"];

drawPies(Data, colorList);