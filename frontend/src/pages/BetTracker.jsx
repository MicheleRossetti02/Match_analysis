/**
 * BetTracker Dashboard
 * 
 * Comprehensive betting performance tracking with:
 * - ROI and Win Rate cards (live updates)
 * - Equity Curve visualization (recharts)
 * - Bet History table with filters
 * - Quick actions to view match details
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import axios from 'axios';

function BetTracker() {
    const [stats, setStats] = useState(null);
    const [equityCurve, setEquityCurve] = useState([]);
    const [betHistory, setBetHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Filters
    const [valueFilter, setValueFilter] = useState('ALL');
    const [statusFilter, setStatusFilter] = useState('ALL');
    
    const [initialBankroll] = useState(1000); // Default starting bankroll

    // Fetch data
    const fetchData = async () => {
        try {
            setLoading(true);
            
            // Fetch performance stats
            const statsRes = await axios.get('/api/bets/stats');
            setStats(statsRes.data);
            
            // Fetch equity curve
            const curveRes = await axios.get(`/api/bets/equity-curve?initial_bankroll=${initialBankroll}`);
            setEquityCurve(curveRes.data);
            
            // Fetch bet history
            const historyParams = new URLSearchParams();
            if (valueFilter !== 'ALL') historyParams.append('value_level', valueFilter);
            if (statusFilter !== 'ALL') historyParams.append('status', statusFilter);
            
            const historyRes = await axios.get(`/api/bets/history?${historyParams}`);
            setBetHistory(historyRes.data);
            
            setLoading(false);
        } catch (error) {
            console.error('Error fetching bet data:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        
        // Auto-refresh every 30 seconds for live updates
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [valueFilter, statusFilter]);

    // Custom tooltip for equity curve
    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-dark-800 border border-dark-600 rounded-lg p-3 shadow-lg">
                    <p className="text-sm text-gray-400 mb-2">
                        {new Date(data.date).toLocaleDateString('it-IT', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </p>
                    <p className="text-white font-bold text-lg">
                        Bankroll: ${data.bankroll.toFixed(2)}
                    </p>
                    <p className={`text-sm font-semibold ${data.cumulative_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        P&L: {data.cumulative_pnl >= 0 ? '+' : ''}${data.cumulative_pnl.toFixed(2)}
                    </p>
                    {data.bet_result && (
                        <p className={`text-xs mt-1 ${data.bet_result === 'WON' ? 'text-green-400' : 'text-red-400'}`}>
                            Last Bet: {data.bet_result} ({data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)})
                        </p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">Bet #{data.bet_count}</p>
                </div>
            );
        }
        return null;
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">📊 Bet Performance Tracker</h1>
                <p className="text-gray-400">Monitor ROI, track wins, and analyze your betting performance</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {/* ROI Card */}
                <div className="card bg-gradient-to-br from-green-600/20 to-emerald-600/20 border-green-500/30">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-gray-400">Total ROI</h3>
                        <span className="text-2xl">💰</span>
                    </div>
                    <p className={`text-4xl font-bold mb-1 ${stats?.roi_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stats?.roi_percent >= 0 ? '+' : ''}{stats?.roi_percent || 0}%
                    </p>
                    <p className="text-sm text-gray-400">
                        {stats?.total_pnl >= 0 ? '+' : ''}${stats?.total_pnl || 0} P&L
                    </p>
                </div>

                {/* Win Rate Card */}
                <div className="card bg-gradient-to-br from-blue-600/20 to-cyan-600/20 border-blue-500/30">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-gray-400">Win Rate</h3>
                        <span className="text-2xl">🎯</span>
                    </div>
                    <p className="text-4xl font-bold text-blue-400 mb-1">
                        {stats?.win_rate || 0}%
                    </p>
                    <p className="text-sm text-gray-400">
                        {stats?.won_bets || 0}W / {stats?.lost_bets || 0}L
                    </p>
                </div>

                {/* Total Bets Card */}
                <div className="card bg-gradient-to-br from-purple-600/20 to-pink-600/20 border-purple-500/30">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-gray-400">Total Bets</h3>
                        <span className="text-2xl">📝</span>
                    </div>
                    <p className="text-4xl font-bold text-purple-400 mb-1">
                        {stats?.total_bets || 0}
                    </p>
                    <p className="text-sm text-gray-400">
                        {stats?.pending_bets || 0} pending
                    </p>
                </div>

                {/* Total Staked Card */}
                <div className="card bg-gradient-to-br from-amber-600/20 to-orange-600/20 border-amber-500/30">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-gray-400">Total Staked</h3>
                        <span className="text-2xl">💵</span>
                    </div>
                    <p className="text-4xl font-bold text-amber-400 mb-1">
                        ${stats?.total_staked || 0}
                    </p>
                    <p className="text-sm text-gray-400">
                        Avg: ${stats?.avg_stake || 0}/bet
                    </p>
                </div>
            </div>

            {/* Equity Curve */}
            <div className="card mb-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-xl font-bold text-white">📈 Equity Curve</h2>
                        <p className="text-sm text-gray-400 mt-1">Bankroll progression over time</p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Starting Bankroll</p>
                        <p className="text-lg font-bold text-white">${initialBankroll}</p>
                    </div>
                </div>

                {equityCurve.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={equityCurve} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis 
                                dataKey="bet_count" 
                                stroke="#9CA3AF"
                                label={{ value: 'Bet Number', position: 'insideBottom', offset: -5, fill: '#9CA3AF' }}
                            />
                            <YAxis 
                                stroke="#9CA3AF"
                                label={{ value: 'Bankroll ($)', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            <Line 
                                type="monotone" 
                                dataKey="bankroll" 
                                stroke="#10B981" 
                                strokeWidth={3}
                                dot={{ fill: '#10B981', r: 4 }}
                                activeDot={{ r: 6 }}
                                name="Bankroll"
                            />
                            <Line 
                                type="monotone" 
                                dataKey={initialBankroll}
                                stroke="#6B7280" 
                                strokeDasharray="5 5"
                                strokeWidth={1}
                                dot={false}
                                name="Initial"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-64 flex items-center justify-center text-gray-400">
                        <div className="text-center">
                            <span className="text-4xl mb-2 block">📊</span>
                            <p>No bets settled yet</p>
                            <p className="text-sm mt-1">Place bets to see your equity curve</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Bet History */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-xl font-bold text-white">📋 Bet History</h2>
                        <p className="text-sm text-gray-400 mt-1">All your placed bets with detailed tracking</p>
                    </div>

                    {/* Filters */}
                    <div className="flex gap-3">
                        <select 
                            value={valueFilter}
                            onChange={(e) => setValueFilter(e.target.value)}
                            className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="ALL">All Values</option>
                            <option value="HIGH">💎 High Value</option>
                            <option value="MEDIUM">⭐ Medium Value</option>
                            <option value="NEUTRAL">⚪ Neutral</option>
                        </select>

                        <select 
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="ALL">All Status</option>
                            <option value="PENDING">⏳ Pending</option>
                            <option value="WON">✅ Won</option>
                            <option value="LOST">❌ Lost</option>
                        </select>
                    </div>
                </div>

                {betHistory.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-dark-700">
                                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Date</th>
                                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Match</th>
                                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Market</th>
                                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-400">Odds</th>
                                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-400">Stake</th>
                                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-400">Kelly%</th>
                                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-400">Value</th>
                                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-400">P&L</th>
                                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {betHistory.map((bet) => (
                                    <tr key={bet.id} className="border-b border-dark-800 hover:bg-dark-700/50 transition-colors">
                                        <td className="py-3 px-4 text-sm text-gray-300">
                                            {new Date(bet.placed_at).toLocaleDateString('it-IT', {
                                                day: '2-digit',
                                                month: 'short'
                                            })}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-white font-medium">
                                            Match #{bet.prediction_id}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-gray-300">
                                            {bet.market_name}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-right text-white font-mono">
                                            {bet.odds.toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-right text-white font-mono">
                                            ${bet.stake_amount.toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                                                bet.stake_kelly_percent >= 15 ? 'bg-red-500/20 text-red-400' :
                                                bet.stake_kelly_percent >= 8 ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-blue-500/20 text-blue-400'
                                            }`}>
                                                {bet.stake_kelly_percent.toFixed(1)}%
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                                                bet.value_level === 'HIGH' ? 'bg-green-500/20 text-green-400' :
                                                bet.value_level === 'MEDIUM' ? 'bg-cyan-500/20 text-cyan-400' :
                                                'bg-gray-500/20 text-gray-400'
                                            }`}>
                                                {bet.value_level === 'HIGH' ? '💎' : bet.value_level === 'MEDIUM' ? '⭐' : '⚪'} {bet.value_level}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                                                bet.status === 'WON' ? 'bg-green-500/20 text-green-400' :
                                                bet.status === 'LOST' ? 'bg-red-500/20 text-red-400' :
                                                'bg-yellow-500/20 text-yellow-400'
                                            }`}>
                                                {bet.status === 'WON' ? '✅' : bet.status === 'LOST' ? '❌' : '⏳'} {bet.status}
                                            </span>
                                        </td>
                                        <td className={`py-3 px-4 text-sm text-right font-bold font-mono ${
                                            bet.pnl > 0 ? 'text-green-400' : bet.pnl < 0 ? 'text-red-400' : 'text-gray-400'
                                        }`}>
                                            {bet.pnl >= 0 ? '+' : ''}${bet.pnl.toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <Link 
                                                to={`/prediction/${bet.prediction?.match_id || bet.prediction_id}`}
                                                className="inline-flex items-center gap-1 px-3 py-1 bg-primary-500/20 text-primary-400 hover:bg-primary-500/30 rounded-lg text-xs font-semibold transition-colors"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                </svg>
                                                View
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="h-48 flex items-center justify-center text-gray-400">
                        <div className="text-center">
                            <span className="text-4xl mb-2 block">📝</span>
                            <p>No bets found</p>
                            <p className="text-sm mt-1">Adjust filters or place your first bet</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Additional Stats */}
            {stats && stats.total_bets > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                    <div className="card">
                        <h3 className="text-lg font-bold text-white mb-4">💎 Value Level Performance</h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">High Value Bets:</span>
                                <span className="text-white font-semibold">{stats.high_value_bets} ({stats.high_value_win_rate}% WR)</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Medium Value Bets:</span>
                                <span className="text-white font-semibold">{stats.medium_value_bets} ({stats.medium_value_win_rate}% WR)</span>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <h3 className="text-lg font-bold text-white mb-4">📊 Betting Stats</h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Average Odds:</span>
                                <span className="text-white font-semibold">{stats.avg_odds}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Best Win:</span>
                                <span className="text-green-400 font-semibold">+${stats.best_win}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Worst Loss:</span>
                                <span className="text-red-400 font-semibold">${stats.worst_loss}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default BetTracker;
