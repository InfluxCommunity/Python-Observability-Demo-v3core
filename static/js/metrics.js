// Chart configuration and initialization
function initCharts() {
  const chartConfigs = [
    {
      id: 'cpuChart',
      label: 'CPU Usage',
      color: 'rgb(75, 192, 192)',
      yAxisMax: 100
    },
    {
      id: 'memoryChart',
      label: 'Memory Usage',
      color: 'rgb(255, 99, 132)',
      yAxisMax: 100
    },
    {
      id: 'networkChart',
      labels: ['Network Bytes Sent', 'Network Bytes Received'],
      colors: ['rgb(54, 162, 235)', 'rgb(255, 206, 86)'],
      multiDataset: true
    },
    {
      id: 'diskChart',
      labels: ['Disk Read (MB)', 'Disk Write (MB)'],
      colors: ['rgb(75, 192, 192)', 'rgb(255, 99, 132)'],
      multiDataset: true
    }
  ];

  return chartConfigs.map(config => createChart(config));
}

function createChart(config) {
  const ctx = document.getElementById(config.id).getContext('2d');

  const datasets = config.multiDataset
    ? config.labels.map((label, index) => ({
      label: label,
      data: [],
      borderColor: config.colors[index],
      tension: 0.1
    }))
    : [{
      label: config.label,
      data: [],
      borderColor: config.color,
      tension: 0.1
    }];

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: datasets
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: config.yAxisMax || undefined
        }
      }
    }
  });

  return chart;
}

// Main metrics handling
function initMetricsHandler() {
  const charts = initCharts();
  const metricElements = {
    cpu: document.getElementById('currentCPU'),
    memory: document.getElementById('currentMemory'),
    memoryUsed: document.getElementById('memoryUsed'),
    networkSent: document.getElementById('networkSent'),
    diskWrite: document.getElementById('diskWrite')
  };

  const eventSource = new EventSource('/metrics-stream');

  eventSource.onmessage = function (event) {
    try {
      const metrics = JSON.parse(event.data);
      const now = new Date().toLocaleTimeString();

      // Update current metrics display
      updateMetricsDisplay(metricElements, metrics);

      // Update charts
      updateCharts(charts, now, metrics);
    } catch (error) {
      console.error('Error processing metrics:', error);
    }
  };

  eventSource.onerror = function (error) {
    console.error('EventSource failed:', error);
    eventSource.close();
  };
}

function updateMetricsDisplay(elements, metrics) {
  elements.cpu.textContent = metrics.cpu_usage.toFixed(2);
  elements.memory.textContent = metrics.memory_usage.toFixed(2);
  elements.memoryUsed.textContent = metrics.memory_used.toFixed(2);
  elements.networkSent.textContent = metrics.network_bytes_sent.toFixed(2);
  elements.diskWrite.textContent = metrics.disk_write_bytes.toFixed(2);
}

function updateCharts(charts, timestamp, metrics) {
  const chartUpdates = [
    { chart: charts[0], value: metrics.cpu_usage },
    { chart: charts[1], value: metrics.memory_usage },
    {
      chart: charts[2],
      values: [metrics.network_bytes_sent, metrics.network_bytes_recv]
    },
    {
      chart: charts[3],
      values: [metrics.disk_read_bytes, metrics.disk_write_bytes]
    }
  ];

  chartUpdates.forEach(update => {
    updateChart(update.chart, timestamp, update.values || update.value);
  });
}

function updateChart(chart, timestamp, values) {
  chart.data.labels.push(timestamp);

  if (Array.isArray(values)) {
    values.forEach((value, index) => {
      chart.data.datasets[index].data.push(value);
    });
  } else {
    chart.data.datasets[0].data.push(values);
  }

  // Limit to last 20 data points
  if (chart.data.labels.length > 20) {
    chart.data.labels.shift();
    chart.data.datasets.forEach(dataset => {
      dataset.data.shift();
    });
  }

  chart.update();
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', initMetricsHandler);