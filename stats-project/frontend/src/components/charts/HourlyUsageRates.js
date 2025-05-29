import { useEffect, useRef, useState } from 'react';
import Plotly from 'plotly.js-dist';

const HourlyUsage = () => {
  const chartRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [noData, setNoData] = useState(false);
  const [timezone, setTimezone] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [chartData, setChartData] = useState(null);

  // Format date for API (YYYY-MM-DD)
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Format date for display
  const displayDate = (date) => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Add days to a date
  const addDays = (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  };

  // Parse date string (YYYY-MM-DD)
  const parseDate = (dateString) => {
    const parts = dateString.split('-');
    return new Date(parts[0], parts[1] - 1, parts[2]);
  };

  // Fetch data when date or timezone changes
  const fetchData = (date, tz) => {
    setLoading(true);
    setError('');
    setNoData(false);
    setChartData(null); // Clear previous data

    fetch(`http://127.0.0.1:8080/api/get_daily_downloads?timezone=${encodeURIComponent(tz)}&date=${formatDate(date)}`)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        if (data.length === 0) throw new Error('No data available');
        setChartData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Fetch error:', err);
        setChartData(null);
        if (err.message === 'No data available') {
          setNoData(true);
        } else {
          setError('Failed to fetch data. Please try again.');
        }
        setLoading(false);
      });
  };

  // Initialize with user's timezone
  useEffect(() => {
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    setTimezone(userTimezone);
    fetchData(selectedDate, userTimezone);
  }, []);

  // Update chart when data changes
  useEffect(() => {
    if (!chartData || !chartRef.current) return;

    // Clean up previous chart if it exists
    if (chartRef.current.data) {
      Plotly.purge(chartRef.current);
    }

    const hours = chartData.map(d => d.hour);
    const totalPrimary = chartData.map(d => d.total_primary);

    const trace = {
      x: hours,
      y: totalPrimary,
      type: 'bar',
      customdata: hours.map(h => {
        if (h === 0) return '12 AM';
        if (h < 12) return `${h} AM`;
        if (h === 12) return '12 PM';
        return `${h - 12} PM`;
      }),
      hovertemplate: '<b>Hour: %{customdata}</b><br>Downloads: %{y:,}<extra></extra>',
      marker: {
        color: totalPrimary,
        colorscale: [
              [0, '#FFD700'],
              [0.125, '#FFC300'],
              [0.25, '#FFB700'],
              [0.375, '#FFAD00'],
              [0.5, '#FFA000'],
              [0.625, '#FF9900'],
              [0.75, '#FF8C00'],
              [0.875, '#FF8400'],
              [1, '#FF7900']
        ],
        cmin: 0,
        cmax: Math.max(...totalPrimary) * 1.1,
        showscale: false
      }
    };

    const layout = {
      margin: { t: 40, r: 30, l: 50, b: 40 },
      title: {
        text: `Hourly Downloads (${displayDate(selectedDate)})<br><sub>Timezone: ${timezone}</sub>`,
        font: { size: 14 }
      },
      xaxis: {
      title: 'Hour of Day',
      tickmode: 'array',
      tickvals: Array.from({ length: 24 }, (_, i) => i + 1),
      ticktext: [
        '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM',
        '7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM',
        '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM',
        '7 PM', '8 PM', '9 PM', '10 PM', '11 PM', '12 AM'
      ],
      range: [0.5, 24.5]  
    },
      yaxis: {
        title: 'Downloads',
        tickformat: ',',
        gridcolor: '#e5e7eb'
      },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      hoverlabel: {
        bgcolor: 'white',
        font: { color: 'black' }
      }
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['toImage', 'sendDataToCloud']
    };

    Plotly.react(chartRef.current, [trace], layout, config);
  }, [chartData, selectedDate, timezone]);

  // Date navigation handlers
  const handlePreviousDay = () => {
    const newDate = addDays(selectedDate, -1);
    setSelectedDate(newDate);
    fetchData(newDate, timezone);
  };

  const handleNextDay = () => {
    const newDate = addDays(selectedDate, 1);
    // Don't allow future dates
    if (newDate <= new Date()) {
      setSelectedDate(newDate);
      fetchData(newDate, timezone);
    }
  };

  const handleDateChange = (e) => {
    const newDate = parseDate(e.target.value);
    // Don't allow future dates
    if (newDate <= new Date()) {
      setSelectedDate(newDate);
      fetchData(newDate, timezone);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <h2 style={{ margin: 0 }}>Daily Download Statistics</h2>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            onClick={handlePreviousDay}
            style={{
              padding: '5px 10px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            ← Previous
          </button>
          
          <input
            type="date"
            value={formatDate(selectedDate)}
            onChange={handleDateChange}
            max={formatDate(new Date())}
            style={{
              padding: '5px',
              border: '1px solid #d1d5db',
              borderRadius: '4px'
            }}
          />
          
          <button 
            onClick={handleNextDay}
            disabled={formatDate(selectedDate) >= formatDate(new Date())}
            style={{
              padding: '5px 10px',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              cursor: formatDate(selectedDate) < formatDate(new Date()) ? 'pointer' : 'not-allowed',
              opacity: formatDate(selectedDate) < formatDate(new Date()) ? 1 : 0.6
            }}
          >
            Next →
          </button>
        </div>
      </div>

      {loading && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '300px',
          color: '#6b7280'
        }}>
          Loading data...
        </div>
      )}

      {error && (
        <div style={{
          padding: '20px',
          background: '#fee2e2',
          color: '#b91c1c',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {noData && (
        <div style={{
          padding: '20px',
          background: '#fef3c7',
          color: '#92400e',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          No data available for {displayDate(selectedDate)}. Please try another date.
        </div>
      )}

      {!loading && !error && !noData && (
        <>
          <div ref={chartRef} style={{ width: '100%', height: '400px' }} />
          <div style={{
            marginTop: '10px',
            fontSize: '12px',
            color: '#6b7280',
            textAlign: 'center'
          }}>
            Timezone: {timezone} | Hover over bars for details
          </div>
        </>
      )}
    </div>
  );
};

export default HourlyUsage;