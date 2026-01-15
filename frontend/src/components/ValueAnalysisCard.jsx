/**
 * Value Analysis Card Component
 * 
 * Displays detailed betting value analysis using Kelly Criterion,
 * Expected Value (EV), and edge percentages.
 */

function ValueAnalysisCard({ prediction, homeTeamName, awayTeamName }) {
    // Check if value analysis is available
    if (!prediction.has_value_analysis || !prediction.estimated_odds) {
        return null; // Don't render if no analysis available
    }

    const {
        kelly_percentage,
        kelly_raw,
        value_level,
        expected_value,
        edge_percentage,
        estimated_odds,
        is_estimated_odds,
        prob_home_win,
        prob_draw,
        prob_away_win
    } = prediction;

    // Calculate implied probabilities from bookmaker odds
    const getImpliedProbability = (odds) => {
        return odds > 0 ? (1 / odds) * 100 : 0;
    };

    // Get best value market
    const markets = [
        {
            name: 'Home Win',
            team: homeTeamName || 'Home',
            aiProb: prob_home_win ? prob_home_win * 100 : 0,
            odds: estimated_odds['1'] || null,
            code: '1'
        },
        {
            name: 'Draw',
            team: 'Draw',
            aiProb: prob_draw ? prob_draw * 100 : 0,
            odds: estimated_odds['X'] || null,
            code: 'X'
        },
        {
            name: 'Away Win',
            team: awayTeamName || 'Away',
            aiProb: prob_away_win ? prob_away_win * 100 : 0,
            odds: estimated_odds['2'] || null,
            code: '2'
        }
    ];

    // Find best value market (highest EV)
    const marketsWithEV = markets
        .filter(m => m.odds && m.aiProb > 0)
        .map(m => ({
            ...m,
            ev: (m.aiProb / 100) * m.odds,
            impliedProb: getImpliedProbability(m.odds),
            edge: ((m.aiProb / 100) * m.odds - 1) * 100
        }))
        .sort((a, b) => b.ev - a.ev);

    const bestMarket = marketsWithEV[0] || null;

    // Value level styling
    const getValueStyle = (level) => {
        switch (level) {
            case 'HIGH':
                return {
                    bg: 'from-green-600/20 to-emerald-600/20',
                    border: 'border-green-500/40',
                    text: 'text-green-400',
                    badge: 'bg-green-500/30 text-green-300 border-green-500',
                    glow: 'shadow-green-500/20'
                };
            case 'MEDIUM':
                return {
                    bg: 'from-cyan-600/20 to-blue-600/20',
                    border: 'border-cyan-500/40',
                    text: 'text-cyan-400',
                    badge: 'bg-cyan-500/30 text-cyan-300 border-cyan-500',
                    glow: 'shadow-cyan-500/20'
                };
            default:
                return {
                    bg: 'from-gray-600/20 to-gray-700/20',
                    border: 'border-gray-500/30',
                    text: 'text-gray-400',
                    badge: 'bg-gray-500/20 text-gray-400 border-gray-500',
                    glow: 'shadow-gray-500/10'
                };
        }
    };

    const style = getValueStyle(value_level);

    return (
        <div className={`card bg-gradient-to-br ${style.bg} border ${style.border}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <span>💰</span>
                        <span>Value Betting Analysis</span>
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">Kelly Criterion & Expected Value</p>
                </div>

                {/* Value Level Badge */}
                <span className={`px-4 py-2 rounded-lg text-sm font-bold uppercase border-2 ${style.badge} shadow-lg ${style.glow}`}>
                    {value_level === 'HIGH' && '💎 '}
                    {value_level === 'MEDIUM' && '⭐ '}
                    {value_level === 'NEUTRAL' && '⛔ '}
                    {value_level || 'NO ANALYSIS'}
                </span>
            </div>

            {/* Best Market Analysis */}
            {bestMarket && (
                <div className="mb-6 p-4 bg-dark-900/50 rounded-lg border border-dark-700">
                    <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-300">Best Value Market</h4>
                        <span className="text-xs text-gray-500 uppercase">{bestMarket.name}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {/* Our Probability */}
                        <div>
                            <p className="text-xs text-gray-400 mb-1">Our Probability</p>
                            <p className="text-2xl font-bold text-primary-400">{bestMarket.aiProb.toFixed(1)}%</p>
                            <p className="text-xs text-gray-500 mt-1">{bestMarket.team}</p>
                        </div>

                        {/* Bookmaker Odds */}
                        <div>
                            <p className="text-xs text-gray-400 mb-1">Bookmaker Odds</p>
                            <p className="text-2xl font-bold text-white">{bestMarket.odds.toFixed(2)}</p>
                            <p className="text-xs text-gray-500 mt-1">Implies {bestMarket.impliedProb.toFixed(1)}%</p>
                        </div>
                    </div>

                    {/* Expected Value */}
                    <div className="mt-4 pt-4 border-t border-dark-700">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-400">Expected Value (EV):</span>
                            <span className={`text-lg font-bold ${bestMarket.ev >= 1.15 ? 'text-green-400' : bestMarket.ev >= 1.05 ? 'text-cyan-400' : 'text-gray-400'}`}>
                                {bestMarket.ev.toFixed(3)}x
                                <span className="text-sm ml-1">
                                    ({bestMarket.edge >= 0 ? '+' : ''}{bestMarket.edge.toFixed(1)}%)
                                </span>
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Kelly Criterion Recommendation */}
            {kelly_percentage !== null && kelly_percentage !== undefined && (
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-300">Kelly Criterion Stake</h4>
                        {is_estimated_odds && (
                            <span className="text-xs text-amber-400 flex items-center gap-1">
                                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                Estimated odds
                            </span>
                        )}
                    </div>

                    {/* Kelly Percentage Bar */}
                    <div className="relative">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-gray-400">Recommended Bankroll %</span>
                            <span className={`text-2xl font-bold ${kelly_percentage > 0 ? style.text : 'text-gray-500'}`}>
                                {kelly_percentage.toFixed(1)}%
                            </span>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full h-8 bg-dark-900 rounded-lg overflow-hidden relative">
                            <div
                                className={`h-full bg-gradient-to-r ${kelly_percentage >= 15 ? 'from-green-500 to-emerald-500' : kelly_percentage >= 8 ? 'from-cyan-500 to-blue-500' : 'from-gray-500 to-gray-600'} transition-all duration-500`}
                                style={{ width: `${Math.min(kelly_percentage / 25 * 100, 100)}%` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-t from-white/10 to-transparent"></div>
                            </div>

                            {/* Scale markers */}
                            <div className="absolute inset-0 flex items-center justify-between px-2 text-xs font-semibold pointer-events-none">
                                <span className={kelly_percentage < 5 ? 'text-white' : 'text-gray-600'}>0%</span>
                                <span className={kelly_percentage > 10 && kelly_percentage < 20 ? 'text-white' : 'text-gray-600'}>15%</span>
                                <span className={kelly_percentage > 20 ? 'text-white' : 'text-gray-600'}>25% Max</span>
                            </div>
                        </div>

                        {/* Risk level */}
                        <div className="mt-2 flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                                {kelly_percentage === 0 && '⛔ No bet recommended'}
                                {kelly_percentage > 0 && kelly_percentage < 5 && '🔵 Low risk'}
                                {kelly_percentage >= 5 && kelly_percentage < 15 && '🟡 Medium risk'}
                                {kelly_percentage >= 15 && '🔴 High risk'}
                            </span>
                            <span className="text-xs text-gray-500">Fractional Kelly (capped at 25%)</span>
                        </div>
                    </div>
                </div>
            )}

            {/* All Markets Comparison */}
            <div className="p-4 bg-dark-900/30 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-300 mb-3">1X2 Markets Comparison</h4>
                <div className="space-y-2">
                    {marketsWithEV.map((market, idx) => (
                        <div key={market.code} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                                <span className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-primary-500/30 text-primary-300' : 'bg-dark-700 text-gray-500'}`}>
                                    {market.code}
                                </span>
                                <span className="text-gray-300">{market.team}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-gray-400">{market.aiProb.toFixed(0)}%</span>
                                <span className="text-white font-semibold">{market.odds.toFixed(2)}</span>
                                <span className={`text-xs ${market.edge >= 15 ? 'text-green-400' : market.edge >= 5 ? 'text-cyan-400' : 'text-gray-500'}`}>
                                    EV: {market.ev.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <div className="flex gap-2">
                    <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <div className="text-xs text-amber-200">
                        <p className="font-semibold mb-1">⚠️ Educational Purpose Only</p>
                        <p className="text-amber-300/80">
                            This analysis is for educational purposes. Betting involves risk of loss.
                            Kelly Criterion recommendations assume accurate probability estimation.
                            Always bet responsibly and within your means.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ValueAnalysisCard;
