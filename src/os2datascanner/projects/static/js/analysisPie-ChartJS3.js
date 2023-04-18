
function displayAsPercentage(value, ctx) {
    const dataArr = ctx.chart.data.datasets[0].data;
    const sum = dataArr.reduce(function (total, frac) { return total + frac; });
    const percentage = Math.round(value * 100 / sum) + "%";
    return value ? percentage : '';
}
  
  
function displayLabelUnit(index, chartObject) {
let dataset = chartObject.datasets[0];
let labelName = chartObject.labels[index];
if (dataset.name === "nfiles"){
    return labelName.concat(": ", formatNumber(dataset.data[index]).toString(), " ", gettext("files"));
}
else if (dataset.name === "storage"){
    return `${labelName}: ${bytesToSize(dataset.data[index])}`;
}
else {
    return `${labelName}: ${formatNumber(dataset.data[index])}`;
}
}

function bytesToSize(bytes) {
const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
if (bytes === 0) {return 'n/a';}
const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
if (i === 0) {return `${bytes} ${sizes[i]}`;}
return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

function formatNumber(x) {
return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function createPie(data, htmlElements, colors){ // jshint ignore:line
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
                position: 'right',
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
                bodyAlign: 'center',
                bodyColor: 'black',
                titleColor: 'black',
                displayColors: false,
                callbacks: {
                    label:(tooltipItem)=>{
                        const name = tooltipItem.dataset.name;
                        const val = tooltipItem.raw;
                        if (name === "storage"){
                            return bytesToSize(val);
                        }
                        else if (name === "nfiles"){
                            if (val === 1){
                                return val.toString().concat(" ", gettext("file"));
                            }   
                            else {
                                return val.toString().concat(" ", gettext("files"));
                            }
                        }
                    },
                    title:(tooltipItem)=>{
                        const label = tooltipItem[0].label;
                        return `${label}:`;
                    },
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

