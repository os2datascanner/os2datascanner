/* exported drawTimelines */

function drawTimelines(snapshotData, pk) {

  let timelinesLineChartLabels = [];
  let timelinesLineChartValues = [];

  for (let point of snapshotData) {
    timelinesLineChartLabels.push(point.x);
    timelinesLineChartValues.push(point.y);
  }

  let timelinesLineChartCtx = document.querySelector("#line_chart_status__" + String(pk));
  if (timelinesLineChartCtx) {
    new Chart(timelinesLineChartCtx, {
      type: 'line',
      data: {
        labels: timelinesLineChartLabels,
        datasets: [{
          data: snapshotData,
          fill: 0,
          tension: 0, // This makes the lines straight, with no curve
          pointRadius: 0,
          pointHitRadius: 20,
          borderWidth: 4,
          borderColor: "#21759c",
          pointHoverRadius: 10,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true, // If false, the charts will not be drawn properly in hidden elements!
        tooltips: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: gettext('Seconds since start of scan')
            }
          },
          y: {
            title: {
              display: true,
              text: gettext('% scanned')
            }
          }
        }
      }
    });
  }
}

function showTimeline(row, toggleButton) {
  let timelinesRow = row.nextElementSibling;
  toggleClass(toggleButton, "up");
  let buttonOpen = hasClass(toggleButton, "up");

  timelinesRow.hidden = !buttonOpen;
}

document.addEventListener("DOMContentLoaded", () => {
  htmx.onLoad(function (content) {
    if (hasClass(content, 'page') || hasClass(content, 'content')) {

      const expandButtons = document.querySelectorAll(".timelines-expand");

      expandButtons.forEach(element => {
        element.addEventListener("click", function (e) {
          targ = e.target;
          let row = closestElement(targ, "tr");
          showTimeline(row, targ);
        });
      });
    } else if (hasClass(content, 'timeline')) {
      let snapshotData = JSON.parse(content.querySelector('#snapshot_data').textContent);
      let pk = JSON.parse(content.querySelector('#status_pk').textContent);

      drawTimelines(snapshotData, pk);
    }
  });
});