document.addEventListener('DOMContentLoaded', function() {
    let performanceChart = null;
    let distributionChart = null;
    let allTrades = [];

    loadData();

    document.getElementById('applyFilters').addEventListener('click', loadData);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
    document.getElementById('addTradeBtn').addEventListener('click', openAddModal);
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('cancelBtn').addEventListener('click', closeModal);
    document.getElementById('tradeForm').addEventListener('submit', saveTrade);

    async function loadData() {
        const params = new URLSearchParams();
        
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const indicator = document.getElementById('indicatorFilter').value;
        const outcome = document.getElementById('outcomeFilter').value;
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (indicator !== 'all') params.append('indicator_type', indicator);
        if (outcome !== 'all') params.append('outcome', outcome);

        try {
            const [statsRes, tradesRes] = await Promise.all([
                fetch(`/api/stats?${params}`),
                fetch(`/api/trades?${params}`)
            ]);

            const statsData = await statsRes.json();
            const tradesData = await tradesRes.json();

            if (statsData.success) {
                updateStats(statsData.stats);
                updateCharts(statsData.stats);
            }

            if (tradesData.success) {
                allTrades = tradesData.trades;
                renderTrades(tradesData.trades);
            }
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    function updateStats(stats) {
        document.getElementById('totalTrades').textContent = stats.total_trades;
        document.getElementById('winningTrades').textContent = stats.winning_trades;
        document.getElementById('losingTrades').textContent = stats.losing_trades;
        document.getElementById('winRate').textContent = `${stats.win_rate}%`;
    }

    function updateCharts(stats) {
        const dates = Object.keys(stats.performance_by_date).sort();
        const wins = dates.map(d => stats.performance_by_date[d].wins);
        const losses = dates.map(d => stats.performance_by_date[d].losses);
        
        if (performanceChart) {
            performanceChart.destroy();
        }
        
        const perfCtx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(perfCtx, {
            type: 'line',
            data: {
                labels: dates.map(d => new Date(d).toLocaleDateString()),
                datasets: [
                    {
                        label: 'Wins',
                        data: wins,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Losses',
                        data: losses,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f8fafc' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    }
                }
            }
        });

        if (distributionChart) {
            distributionChart.destroy();
        }

        const distCtx = document.getElementById('distributionChart').getContext('2d');
        distributionChart = new Chart(distCtx, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Losses', 'Pending'],
                datasets: [{
                    data: [stats.winning_trades, stats.losing_trades, stats.pending_trades],
                    backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                    borderColor: '#1e293b',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f8fafc' }
                    }
                }
            }
        });
    }

    function renderTrades(trades) {
        const tbody = document.getElementById('tradesBody');
        const emptyMessage = document.getElementById('emptyMessage');
        
        if (trades.length === 0) {
            tbody.innerHTML = '';
            emptyMessage.style.display = 'block';
            return;
        }
        
        emptyMessage.style.display = 'none';
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${trade.created_at ? new Date(trade.created_at).toLocaleDateString() : 'N/A'}</td>
                <td>${trade.symbol || 'N/A'}</td>
                <td class="${getRecommendationClass(trade.recommendation)}">${trade.recommendation || 'N/A'}</td>
                <td>${trade.indicator_type || 'N/A'}</td>
                <td class="${getOutcomeClass(trade.outcome)}">${formatOutcome(trade.outcome)}</td>
                <td class="${trade.profit_loss >= 0 ? 'profit' : 'loss'}">${trade.profit_loss !== null ? formatPL(trade.profit_loss) : 'N/A'}</td>
                <td>
                    <button class="btn-icon" onclick="editTrade(${trade.id})" title="Edit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon danger" onclick="deleteTrade(${trade.id})" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    function getRecommendationClass(rec) {
        if (!rec) return '';
        rec = rec.toLowerCase();
        if (rec.includes('buy')) return 'buy';
        if (rec.includes('sell')) return 'sell';
        return 'hold';
    }

    function getOutcomeClass(outcome) {
        if (!outcome) return 'pending';
        return outcome.toLowerCase();
    }

    function formatOutcome(outcome) {
        if (!outcome || outcome === 'pending') return 'Pending';
        return outcome.charAt(0).toUpperCase() + outcome.slice(1);
    }

    function formatPL(value) {
        const formatted = value.toFixed(2);
        return value >= 0 ? `+$${formatted}` : `-$${Math.abs(value).toFixed(2)}`;
    }

    function clearFilters() {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('indicatorFilter').value = 'all';
        document.getElementById('outcomeFilter').value = 'all';
        loadData();
    }

    function openAddModal() {
        document.getElementById('modalTitle').textContent = 'Add Trade';
        document.getElementById('tradeForm').reset();
        document.getElementById('tradeId').value = '';
        document.getElementById('tradeModal').style.display = 'flex';
    }

    function closeModal() {
        document.getElementById('tradeModal').style.display = 'none';
    }

    window.editTrade = function(id) {
        const trade = allTrades.find(t => t.id === id);
        if (!trade) return;
        
        document.getElementById('modalTitle').textContent = 'Edit Trade';
        document.getElementById('tradeId').value = trade.id;
        document.getElementById('symbol').value = trade.symbol || '';
        document.getElementById('recommendation').value = trade.recommendation || 'HOLD';
        document.getElementById('indicatorType').value = trade.indicator_type || 'Combined';
        document.getElementById('outcome').value = trade.outcome || 'pending';
        document.getElementById('entryPrice').value = trade.entry_price || '';
        document.getElementById('exitPrice').value = trade.exit_price || '';
        document.getElementById('profitLoss').value = trade.profit_loss || '';
        document.getElementById('notes').value = trade.notes || '';
        
        document.getElementById('tradeModal').style.display = 'flex';
    };

    window.deleteTrade = async function(id) {
        if (!confirm('Are you sure you want to delete this trade?')) return;
        
        try {
            const response = await fetch(`/api/trades/${id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                loadData();
            } else {
                alert('Error deleting trade: ' + data.error);
            }
        } catch (error) {
            alert('Error deleting trade: ' + error.message);
        }
    };

    async function saveTrade(e) {
        e.preventDefault();
        
        const tradeId = document.getElementById('tradeId').value;
        const tradeData = {
            symbol: document.getElementById('symbol').value,
            recommendation: document.getElementById('recommendation').value,
            indicator_type: document.getElementById('indicatorType').value,
            outcome: document.getElementById('outcome').value,
            entry_price: parseFloat(document.getElementById('entryPrice').value) || null,
            exit_price: parseFloat(document.getElementById('exitPrice').value) || null,
            profit_loss: parseFloat(document.getElementById('profitLoss').value) || null,
            notes: document.getElementById('notes').value
        };
        
        try {
            const url = tradeId ? `/api/trades/${tradeId}` : '/api/trades';
            const method = tradeId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(tradeData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                closeModal();
                loadData();
            } else {
                alert('Error saving trade: ' + data.error);
            }
        } catch (error) {
            alert('Error saving trade: ' + error.message);
        }
    }
});
