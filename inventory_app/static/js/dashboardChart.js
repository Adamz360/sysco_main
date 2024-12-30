document.addEventListener('DOMContentLoaded', () => {
    const { months, revenues, profits } = chartData;

    const ctx = document.getElementById('revenueProfitChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: months.map(month =>
                new Date(2000, month - 1).toLocaleString('default', { month: 'long' })
            ),
            datasets: [
                {
                    label: 'Revenue',
                    data: revenues,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
                {
                    label: 'Profit',
                    data: profits,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Months',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount (NGN)',
                    },
                    beginAtZero: true,
                },
            },
        },
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const { days, revenues, profits, expenses } = chartData_day;

    const ctx = document.getElementById('dailyRevenueProfitChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: days, // Display the list of days as-is
            datasets: [
                {
                    label: 'Revenue',
                    data: revenues,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
                {
                    label: 'Profit',
                    data: profits,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
                {
                    label: 'Expense',
                    data: expenses,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Days',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount (NGN)',
                    },
                    beginAtZero: true,
                },
            },
        },
    });
});
