import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

function Bolletta() {
    // Fetch more predictions (20 matches for comprehensive betting slip)
    const { data: predictions, isLoading } = useQuery({
        queryKey: ['bollettaPredictions'],
        queryFn: () => api.getUpcomingPredictions({ days: 7, limit: 20 }),
    })

    // Extract the BEST bet from each prediction (one per match)
    const extractBestBetPerMatch = (predictionsData) => {
        if (!predictionsData) return [];

        // Map to store best bet per match
        const bestBetByMatch = new Map();

        predictionsData.forEach(prediction => {
            const match = prediction.match;
            const matchId = prediction.match_id;
            const matchInfo = {
                matchId: matchId,
                homeTeam: match?.home_team?.name || 'Home',
                awayTeam: match?.away_team?.name || 'Away',
                homeLogo: match?.home_team?.logo,
                awayLogo: match?.away_team?.logo,
                matchDate: match?.match_date
            };

            // Collect all possible bets for this match
            const betsForMatch = [];

            // 1X2 bets
            if (prediction.prob_home_win && prediction.prob_home_win >= 0.50) {
                betsForMatch.push({ ...matchInfo, betType: '1', betLabel: 'Home Win', probability: prediction.prob_home_win, color: 'blue', category: '1X2' });
            }
            if (prediction.prob_draw && prediction.prob_draw >= 0.40) {
                betsForMatch.push({ ...matchInfo, betType: 'X', betLabel: 'Draw', probability: prediction.prob_draw, color: 'gray', category: '1X2' });
            }
            if (prediction.prob_away_win && prediction.prob_away_win >= 0.50) {
                betsForMatch.push({ ...matchInfo, betType: '2', betLabel: 'Away Win', probability: prediction.prob_away_win, color: 'purple', category: '1X2' });
            }

            // BTTS (Both Teams To Score)
            if (prediction.btts_confidence) {
                if (prediction.btts_prediction && prediction.btts_confidence >= 0.55) {
                    betsForMatch.push({ ...matchInfo, betType: 'GG', betLabel: 'BTTS Yes', probability: prediction.btts_confidence, color: 'green', category: 'BTTS' });
                } else if (!prediction.btts_prediction && prediction.btts_confidence >= 0.55) {
                    betsForMatch.push({ ...matchInfo, betType: 'NG', betLabel: 'BTTS No', probability: prediction.btts_confidence, color: 'red', category: 'BTTS' });
                }
            }

            // Over/Under 2.5
            if (prediction.over_25_confidence) {
                if (prediction.over_25_prediction && prediction.over_25_confidence >= 0.55) {
                    betsForMatch.push({ ...matchInfo, betType: 'O2.5', betLabel: 'Over 2.5', probability: prediction.over_25_confidence, color: 'teal', category: 'Goals' });
                } else if (!prediction.over_25_prediction) {
                    const under25Prob = 1 - prediction.over_25_confidence;
                    if (under25Prob >= 0.55) {
                        betsForMatch.push({ ...matchInfo, betType: 'U2.5', betLabel: 'Under 2.5', probability: under25Prob, color: 'orange', category: 'Goals' });
                    }
                }
            }

            // Over 1.5 (usually high probability)
            if (prediction.over_15_prediction) {
                betsForMatch.push({ ...matchInfo, betType: 'O1.5', betLabel: 'Over 1.5', probability: 0.82, color: 'cyan', category: 'Goals' });
            }

            // Multi-goal prediction
            if (prediction.multi_goal_prediction && prediction.multi_goal_confidence >= 0.50) {
                betsForMatch.push({ ...matchInfo, betType: prediction.multi_goal_prediction, betLabel: `${prediction.multi_goal_prediction} Goals`, probability: prediction.multi_goal_confidence, color: 'amber', category: 'Goals' });
            }

            // ========== DOUBLE CHANCE (Dixon-Coles) ==========
            // Safe bets with higher win probability (≥70%)
            if (prediction.prob_1x && prediction.prob_1x >= 0.70) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: '1X',
                    betLabel: 'DC 1X',
                    probability: prediction.prob_1x,
                    color: 'emerald',
                    category: 'Double Chance',
                    isSafe: true
                });
            }

            if (prediction.prob_12 && prediction.prob_12 >= 0.70) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: '12',
                    betLabel: 'DC 12',
                    probability: prediction.prob_12,
                    color: 'violet',
                    category: 'Double Chance',
                    isSafe: true
                });
            }

            if (prediction.prob_x2 && prediction.prob_x2 >= 0.70) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: 'X2',
                    betLabel: 'DC X2',
                    probability: prediction.prob_x2,
                    color: 'blue',
                    category: 'Double Chance',
                    isSafe: true
                });
            }

            // ========== COMBO PREDICTIONS (Dixon-Coles) ==========
            // High value bets (≥40% threshold)
            const combos = prediction.combo_predictions || {};

            if (combos['1_over_25'] && combos['1_over_25'] >= 0.40) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: '1_O2.5',
                    betLabel: '1+Over2.5',
                    probability: combos['1_over_25'],
                    color: 'gold',
                    category: 'Combo',
                    isValue: true
                });
            }

            if (combos['x_under_25'] && combos['x_under_25'] >= 0.40) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: 'X_U2.5',
                    betLabel: 'X+Under2.5',
                    probability: combos['x_under_25'],
                    color: 'silver',
                    category: 'Combo',
                    isValue: true
                });
            }

            if (combos['gg_over_25'] && combos['gg_over_25'] >= 0.40) {
                betsForMatch.push({
                    ...matchInfo,
                    betType: 'GG_O2.5',
                    betLabel: 'GG+Over2.5',
                    probability: combos['gg_over_25'],
                    color: 'gold',
                    category: 'Combo',
                    isValue: true
                });
            }

            // Find the best bet for this match (highest probability)
            if (betsForMatch.length > 0) {
                const bestBet = betsForMatch.reduce((best, current) =>
                    current.probability > best.probability ? current : best
                );
                bestBetByMatch.set(matchId, bestBet);
            }
        });

        // Convert map to array and sort by probability
        return Array.from(bestBetByMatch.values()).sort((a, b) => b.probability - a.probability);
    };

    const allBets = extractBestBetPerMatch(predictions?.data);
    const bollettaPicks = allBets.slice(0, 10); // Top 10 unique matches for the bolletta

    // Calculate combined probability for bolletta
    const combinedProbability = bollettaPicks.reduce((acc, bet) => acc * bet.probability, 1);
    const combinedPercentage = (combinedProbability * 100).toFixed(2);
    const impliedOdds = (1 / combinedProbability).toFixed(2);

    // Color mapping
    const colorMap = {
        blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
        gray: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
        green: 'bg-green-500/20 text-green-400 border-green-500/30',
        red: 'bg-red-500/20 text-red-400 border-red-500/30',
        teal: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
        orange: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        cyan: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
        amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',  // DC
        violet: 'bg-violet-500/20 text-violet-400 border-violet-500/30',      // DC
        gold: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',       // Combo
        silver: 'bg-slate-500/20 text-slate-400 border-slate-500/30'         // Combo
    };

    if (isLoading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto"></div>
                <p className="text-gray-400 mt-4">Loading betting slip...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Back Button */}
            <Link to="/" className="inline-flex items-center text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Dashboard
            </Link>

            {/* Header */}
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-white flex items-center justify-center gap-3">
                    <span className="text-5xl">🎫</span>
                    Bolletta della Settimana
                </h1>
                <p className="text-gray-400 text-lg">
                    AI-powered accumulator with Dixon-Coles advanced markets
                </p>
            </div>

            {/* Main Bolletta Card */}
            {bollettaPicks.length >= 3 ? (
                <div className="card bg-gradient-to-br from-emerald-900/30 to-emerald-700/10 border-emerald-500/40 overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between pb-6 border-b border-emerald-500/20 mb-6">
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center">
                                <span className="text-4xl">🎰</span>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-emerald-400">Smart Accumulator</h2>
                                <p className="text-gray-400">Top {bollettaPicks.length} best bets from {predictions?.data?.length || 0} matches</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-4xl font-bold text-emerald-400">{impliedOdds}x</p>
                            <p className="text-sm text-gray-500">potential multiplier</p>
                        </div>
                    </div>

                    {/* Selections */}
                    <div className="space-y-3 mb-6">
                        {bollettaPicks.map((bet, idx) => (
                            <Link
                                key={`${bet.matchId}-${bet.betType}-${idx}`}
                                to={`/match/${bet.matchId}`}
                                className="flex items-center justify-between bg-dark-800/50 rounded-lg p-4 border border-dark-600 hover:border-emerald-500/50 transition-all group"
                            >
                                <div className="flex items-center gap-4 flex-1 min-w-0">
                                    <span className="text-lg font-bold bg-emerald-500/20 text-emerald-400 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
                                        {idx + 1}
                                    </span>
                                    <div className="flex items-center gap-3 min-w-0">
                                        {bet.homeLogo && (
                                            <img src={bet.homeLogo} alt="" className="w-8 h-8 object-contain flex-shrink-0" />
                                        )}
                                        <div className="min-w-0">
                                            <p className="text-white font-medium truncate">
                                                {bet.homeTeam} vs {bet.awayTeam}
                                            </p>
                                            {bet.matchDate && (
                                                <p className="text-xs text-gray-500">
                                                    {new Date(bet.matchDate).toLocaleDateString('en-US', {
                                                        weekday: 'short',
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </p>
                                            )}
                                        </div>
                                        {bet.awayLogo && (
                                            <img src={bet.awayLogo} alt="" className="w-8 h-8 object-contain flex-shrink-0" />
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-4 flex-shrink-0">
                                    <span className={`text-sm font-bold px-3 py-1.5 rounded-lg border ${colorMap[bet.color]}`}>
                                        {bet.betLabel}
                                        {bet.isSafe && <span className="ml-1.5">🛡️</span>}
                                        {bet.isValue && <span className="ml-1.5">💎</span>}
                                    </span>
                                    <span className="text-emerald-400 font-bold text-lg">
                                        {(bet.probability * 100).toFixed(0)}%
                                    </span>
                                    <svg className="w-5 h-5 text-gray-600 group-hover:text-emerald-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </Link>
                        ))}
                    </div>

                    {/* Footer - Combined Stats */}
                    <div className="bg-emerald-500/10 rounded-lg p-6 border border-emerald-500/20">
                        <div className="grid grid-cols-3 gap-6 text-center">
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Combined Probability</p>
                                <p className="text-3xl font-bold text-white">{combinedPercentage}%</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Total Selections</p>
                                <p className="text-3xl font-bold text-emerald-400">{bollettaPicks.length}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">If All Correct</p>
                                <p className="text-3xl font-bold text-emerald-400">€10 → €{(10 * parseFloat(impliedOdds)).toFixed(2)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="card text-center py-12">
                    <div className="text-6xl mb-4">🔮</div>
                    <h3 className="text-xl font-bold text-white mb-2">Not Enough Predictions</h3>
                    <p className="text-gray-400">
                        We need at least 3 high-confidence predictions to build a bolletta.
                    </p>
                </div>
            )}

            {/* All Available Bets Section */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white">📊 All Available Bets ({allBets.length})</h2>
                <p className="text-gray-400">All predictions sorted by probability - click to view match details</p>

                <div className="grid gap-3">
                    {allBets.map((bet, idx) => (
                        <Link
                            key={`all-${bet.matchId}-${bet.betType}-${idx}`}
                            to={`/match/${bet.matchId}`}
                            className="card hover:border-primary-500/50 transition-all group flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <span className="text-sm font-bold text-gray-500 w-6">#{idx + 1}</span>
                                <div className="flex items-center gap-2">
                                    {bet.homeLogo && <img src={bet.homeLogo} alt="" className="w-6 h-6 object-contain" />}
                                    <span className="text-white font-medium">{bet.homeTeam}</span>
                                    <span className="text-gray-500">vs</span>
                                    <span className="text-white font-medium">{bet.awayTeam}</span>
                                    {bet.awayLogo && <img src={bet.awayLogo} alt="" className="w-6 h-6 object-contain" />}
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-gray-500 uppercase">{bet.category}</span>
                                <span className={`text-xs font-bold px-2 py-1 rounded ${colorMap[bet.color]}`}>
                                    {bet.betLabel}
                                </span>
                                <span className={`font-bold ${bet.probability >= 0.80 ? 'text-emerald-400' :
                                    bet.probability >= 0.65 ? 'text-yellow-400' : 'text-gray-400'
                                    }`}>
                                    {(bet.probability * 100).toFixed(0)}%
                                </span>
                                <svg className="w-4 h-4 text-gray-600 group-hover:text-primary-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Disclaimer */}
            <div className="text-center text-xs text-gray-500">
                <p>⚠️ AI predictions for entertainment only. Gamble responsibly. 18+ only.</p>
            </div>
        </div>
    )
}

export default Bolletta
