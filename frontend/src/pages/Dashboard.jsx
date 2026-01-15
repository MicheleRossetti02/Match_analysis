import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { useBetSlip } from '../context/BetSlipContext'
import { Plus } from 'lucide-react'

// League flag mapping
const LEAGUE_FLAGS = {
    'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'Serie A': '🇮🇹',
    'La Liga': '🇪🇸',
    'Bundesliga': '🇩🇪',
    'Ligue 1': '🇫🇷'
}

// Helper: Calculate Expected Value (Defensive)
function calculateEV(prob, odds) {
    if (!prob || !odds || prob <= 0 || odds <= 0) return 0;
    return (prob * odds) - 1;
}

// Helper: Estimate odds from probability (Defensive)
function estimateOdds(prob) {
    if (!prob || prob <= 0) return 1.0;
    return Math.max(1.0, 1 / prob);
}

function Dashboard() {
    const { addBet } = useBetSlip();

    // Fetch upcoming predictions
    const { data: predictions, isLoading: loadingPredictions } = useQuery({
        queryKey: ['upcomingPredictions'],
        queryFn: () => api.getUpcomingPredictions({ days: 7, limit: 15 }),
    })

    // Fetch leagues
    const { data: leagues, isLoading: loadingLeagues } = useQuery({
        queryKey: ['leagues'],
        queryFn: () => api.getLeagues(),
    })

    // Fetch accuracy stats
    const { data: accuracyStats } = useQuery({
        queryKey: ['accuracyStats'],
        queryFn: () => api.getAccuracyStats(),
    })

    // Handler: Add bet to slip
    const handleAddToBetSlip = (prediction, market) => {
        if (!prediction?.match) return;

        const probability = market === '1' ? (prediction.prob_home_win || 0) :
            market === 'X' ? (prediction.prob_draw || 0) :
                (prediction.prob_away_win || 0);

        if (probability <= 0) return;

        const odds = estimateOdds(probability);
        addBet(prediction.match, prediction, market, odds);
    };

    // Prepare predictions with EV
    const preparedPredictions = (predictions?.data || []).map(pred => {
        const ev1 = calculateEV(pred.prob_home_win || 0, estimateOdds(pred.prob_home_win || 0));
        const evX = calculateEV(pred.prob_draw || 0, estimateOdds(pred.prob_draw || 0));
        const ev2 = calculateEV(pred.prob_away_win || 0, estimateOdds(pred.prob_away_win || 0));
        const maxEV = Math.max(ev1, evX, ev2, 0);

        return { ...pred, maxEV };
    }).sort((a, b) => b.maxEV - a.maxEV);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center space-y-4">
                <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-400 to-blue-500 bg-clip-text text-transparent">
                    Football Match Predictions
                </h1>
                <p className="text-gray-400 text-lg">
                    AI-powered predictions for Europe's Top 5 Football Leagues
                </p>
            </div>

            {/* Stats Cards */}
            {accuracyStats?.data && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="card bg-gradient-to-br from-primary-600/20 to-primary-800/20 border-primary-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Model Accuracy</h3>
                        <p className="text-4xl font-bold text-primary-400 mt-2">
                            {accuracyStats.data.accuracy_percent?.toFixed(1) || '0.0'}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            {accuracyStats.data.total_predictions || 0} predictions analyzed
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Active Model</h3>
                        <p className="text-2xl font-bold text-blue-400 mt-2">
                            {accuracyStats.data.active_model?.type || 'Training...'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            v{accuracyStats.data.active_model?.version || '0.0.0'}
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-purple-600/20 to-purple-800/20 border-purple-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Supported Leagues</h3>
                        <p className="text-4xl font-bold text-purple-400 mt-2">5</p>
                        <p className="text-xs text-gray-500 mt-1">European top divisions</p>
                    </div>
                </div>
            )}

            {/* Leagues Section */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white">Select a League</h2>

                {loadingLeagues ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                        <p className="text-gray-400 mt-4">Loading leagues...</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {(leagues?.data || [])
                            .filter((league, index, self) =>
                                index === self.findIndex((l) => l.name === league.name)
                            )
                            .map((league) => (
                                <Link
                                    key={league.id}
                                    to={`/leagues/${league.id}`}
                                    className="card hover:border-primary-500/50 hover:shadow-xl hover:shadow-primary-500/10 transition-all duration-300 group"
                                >
                                    <div className="flex items-center space-x-4">
                                        <div className="text-5xl group-hover:scale-110 transition-transform">
                                            {LEAGUE_FLAGS[league.name] || '⚽'}
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="text-xl font-bold text-white group-hover:text-primary-400 transition-colors">
                                                {league.name}
                                            </h3>
                                            <p className="text-sm text-gray-400">{league.country}</p>
                                            <p className="text-xs text-gray-500 mt-1">Season {league.season}</p>
                                        </div>
                                        <div className="text-gray-600 group-hover:text-primary-500 transition-colors">
                                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                    </div>
                )}

                {!loadingLeagues && (!leagues?.data || leagues.data.length === 0) && (
                    <div className="card text-center py-12">
                        <div className="text-6xl mb-4">⚽</div>
                        <h3 className="text-xl font-bold text-white mb-2">No Leagues Available Yet</h3>
                        <p className="text-gray-400">
                            Data collection is in progress. Leagues will appear here soon.
                        </p>
                    </div>
                )}
            </div>

            {/* Bolletta Banner */}
            <Link
                to="/bolletta"
                className="card bg-gradient-to-r from-emerald-900/40 to-teal-800/40 border-emerald-500/40 hover:border-emerald-400/60 transition-all group block"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 bg-emerald-500/20 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                            <span className="text-3xl">🎫</span>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-emerald-400">Bolletta della Settimana</h2>
                            <p className="text-gray-400">View the AI-powered accumulator with best bets across all markets</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-500">View all picks</span>
                        <svg className="w-6 h-6 text-emerald-400 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </div>
                </div>
            </Link>

            {/* Top Picks - EV Ranked */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-white">🏆 Top Picks of the Week</h2>
                    <span className="text-sm text-gray-500">Ranked by Expected Value (EV)</span>
                </div>

                {loadingPredictions ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                    </div>
                ) : preparedPredictions.length > 0 ? (
                    <div className="space-y-3">
                        {preparedPredictions.map((prediction, index) => {
                            const rankStyles = [
                                { icon: '🥇', border: 'border-yellow-500/50', bg: 'bg-yellow-500/10' },
                                { icon: '🥈', border: 'border-gray-400/50', bg: 'bg-gray-400/10' },
                                { icon: '🥉', border: 'border-amber-600/50', bg: 'bg-amber-600/10' },
                            ];
                            const style = rankStyles[index] || { icon: null, border: 'border-dark-700', bg: '' };

                            return (
                                <Link
                                    key={prediction.id}
                                    to={`/match/${prediction.match_id}`}
                                    className={`card ${style.border} ${style.bg} hover:border-primary-500/50 transition-all group block`}
                                >
                                    <div className="flex items-center gap-4">
                                        {/* Rank */}
                                        <div className="text-2xl w-10 text-center flex-shrink-0">
                                            {style.icon || <span className="text-gray-600 font-bold">#{index + 1}</span>}
                                        </div>

                                        {/* Match Info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 flex-wrap">
                                                <div className="flex items-center gap-2">
                                                    {prediction.match?.home_team?.logo && (
                                                        <img
                                                            src={prediction.match.home_team.logo}
                                                            alt=""
                                                            className="w-6 h-6 object-contain"
                                                        />
                                                    )}
                                                    <span className="font-semibold text-white">
                                                        {prediction.match?.home_team?.name || 'Home'}
                                                    </span>
                                                </div>

                                                <span className="text-gray-500">vs</span>

                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-white">
                                                        {prediction.match?.away_team?.name || 'Away'}
                                                    </span>
                                                    {prediction.match?.away_team?.logo && (
                                                        <img
                                                            src={prediction.match.away_team.logo}
                                                            alt=""
                                                            className="w-6 h-6 object-contain"
                                                        />
                                                    )}
                                                </div>
                                            </div>

                                            {prediction.match?.match_date && (
                                                <p className="text-sm text-gray-500 mt-1">
                                                    📅 {new Date(prediction.match.match_date).toLocaleDateString('en-US', {
                                                        weekday: 'short',
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </p>
                                            )}
                                        </div>

                                        {/* Prediction Info & 1-X-2 Buttons */}
                                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                                            {/* EV Badge */}
                                            {prediction.maxEV > 0.05 && (
                                                <span className="badge badge-success text-xs">
                                                    EV: +{(prediction.maxEV * 100).toFixed(1)}%
                                                </span>
                                            )}

                                            {/* Confidence */}
                                            <span className={`badge ${(prediction.confidence || 0) > 0.7 ? 'badge-success' :
                                                (prediction.confidence || 0) > 0.5 ? 'badge-warning' : 'badge-info'
                                                }`}>
                                                {((prediction.confidence || 0) * 100).toFixed(0)}% confidence
                                            </span>

                                            {/* AI Prediction */}
                                            <p className="text-sm text-gray-400 font-medium">
                                                {prediction.predicted_result === 'H' ? '🏠 Home Win' :
                                                    prediction.predicted_result === 'A' ? '✈️ Away Win' :
                                                        prediction.predicted_result === 'D' ? '🤝 Draw' : 'Unknown'}
                                            </p>

                                            {/* 1-X-2 Buttons */}
                                            <div className="flex gap-1 mt-2">
                                                {['1', 'X', '2'].map(market => {
                                                    const prob = market === '1' ? (prediction.prob_home_win || 0) :
                                                        market === 'X' ? (prediction.prob_draw || 0) :
                                                            (prediction.prob_away_win || 0);
                                                    const odds = estimateOdds(prob);

                                                    return (
                                                        <button
                                                            key={market}
                                                            onClick={(e) => {
                                                                e.preventDefault();
                                                                e.stopPropagation();
                                                                handleAddToBetSlip(prediction, market);
                                                            }}
                                                            className="px-3 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded border border-green-500/30 transition-colors"
                                                            title={`Add ${market} to Bet Slip`}
                                                        >
                                                            <div className="flex flex-col items-center">
                                                                <span className="font-bold text-xs">{market}</span>
                                                                <span className="text-[10px]">{odds.toFixed(2)}</span>
                                                            </div>
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        {/* Arrow */}
                                        <div className="text-gray-600 group-hover:text-primary-500 transition-colors flex-shrink-0">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                ) : (
                    <div className="card text-center py-8">
                        <div className="text-4xl mb-3">🔮</div>
                        <h3 className="text-lg font-bold text-white mb-1">No Predictions Yet</h3>
                        <p className="text-gray-400 text-sm">
                            Predictions will appear here once generated for upcoming matches.
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Dashboard
