let allFilesToCatch = [
  "长江_寸滩.csv",
  "乌江_武隆.csv",
  "长江_三峡水库.csv", //2
  "长江_茅坪(二).csv",
  "长江_宜昌.csv",
  "长江_沙市.csv",
  "长江_城陵矶(莲).csv",
  "洞庭湖_城陵矶(七).csv",
  "汉江_丹江口水库.csv", //8
  "汉江_龙王庙.csv",
  "长江_汉口.csv",
  "长江_九江.csv",
  "鄱阳湖_湖口.csv",
  "长江_大通.csv",
];
const allCharts = document.getElementById('allCharts');

var genChart = function(fileOrder, chartId , type = 'station') {
  let config = {
    bindto: document.getElementById(chartId),
    data: {
//       url: `https://cdn.jsdelivr.net/gh/cxumol/LongRiver@master/data/2020-07/${allFilesToCatch[fileOrder]}`,
      url: `https://raw.githack.com/cxumol/LongRiver/master/data/2020-07/${allFilesToCatch[fileOrder]}`,
      x: 'tm',
      hide: ['oq', 'stcd', 'wptn',  'rvnm', 'stnm'],
      names: {
        q: '流量 (m3/s)',
        z: '水位 (m)'
      },
      axes: {
        q: 'y',
        z: 'y2'
      }
    },
    legend: {
      hide: ['oq', 'stcd', 'wptn', 'rvnm', 'stnm']
    },
    axis: {
      x: {
        //type: 'time',
        tick: {
          count: 7,
          format: function(x) {
            return new Date(x).toLocaleDateString('zh-CN');
          } //toLocaleDateString
        }
      },
      y: {
        label: {
          text: 'Q (m3/s)',
          position: 'outer-top'
        },
      },
      y2: {
        show: true,
        label: 'Stage (m)'
      }
    },
    tooltip: {
      format: {
        title: function(x, index) {
          return new Date(x).toLocaleString('zh-CN');
        }
      }
    }
  };
  if (type  === 'reservoir') {
        config.data.names.q = '入流量 (m3/s)'; 
    config.data.names.oq = '出流量 (m3/s)';
    delete config.data.hide[0];
    delete config.legend.hide[0];
  }
  return c3.generate(config);
}


for (let fileOrder = 0; fileOrder < allFilesToCatch.length; fileOrder++) {
  //console.log(fileOrder);
  let chart = document.createElement('div');
  chart.id = `chart-${fileOrder}`;

  let chartTitle = document.createElement('h4');
  chartTitle.innerHTML = allFilesToCatch[fileOrder].slice(0, -4).replace('_',' ');

  allCharts.append(chartTitle);
  allCharts.append(chart);
  if ( allFilesToCatch[fileOrder].includes('水库') ) {
    genChart(fileOrder, chart.id,  type  = 'reservoir');
  } else {
  genChart(fileOrder, chart.id); 
  }
}
