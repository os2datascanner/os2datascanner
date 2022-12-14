function drawUserChart(content) {

  const matchesByWeek = JSON.parse(content.querySelector('#matches_by_week').textContent);
  const accountUuid = JSON.parse(content.querySelector('#uuid').textContent);

  let weeknums = [];
  let matches = [];

  for (let obj of matchesByWeek) {
    // Reverse the direction of the arrays with unshift.
    weeknums.unshift(obj.weeknum);
    matches.unshift(obj.matches);
  }

  const UserChartCtx = document.querySelector("#line_chart_all_matches_development__" + accountUuid).getContext('2d');

  makeLineChart(weeknums, matches, UserChartCtx, xLabel = "Uge", yLabel = "Uhåndterede resultater");


}

htmx.onLoad((content) => {
  if (hasClass(content, 'overview_wrapper') || hasClass(content, 'page')) {
    drawUserChart(content);
  }
});
