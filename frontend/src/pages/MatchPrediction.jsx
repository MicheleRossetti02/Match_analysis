import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { format } from 'date-fns'

function MatchPrediction() {
    const { matchId } = useParams()

    // Fetch match details
    const { data: match, isLoading: loadingMatch } = useQuery({
        queryKey: ['match', matchId],
        queryFn: () => api.getMatch(matchId),
    })

    // Fetch prediction
    const { data: prediction, isLoading: loadingPrediction, error } = useQuery({
        queryKey: ['prediction', matchId],
        queryFn: () => api.getMatchPrediction(matchId),
        enabled: !!matchId,
        retry: false,
    })

    if (loadingMatch || loadingPrediction) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                <p className="text-gray-400 mt-4">Loading prediction...</p>
            </div>
        )
    }

    const matchData = match?.data
    const predictionData = prediction?.data

    return (
        <div className="space-y-8 max-w-4xl mx-auto">
            {/* Back Button */}
            <Link to="/" className="inline-flex items-center text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back
            </Link>

            {/* Match Header */}
            {matchData && (
                <div className="card">
                    <div className="text-center mb-6">
                        <p className="text-gray-400 text-sm">
                            {format(new Date(matchData.match_date), 'PPPP')}
                        </p>
                        <p className="text-gray-400 text-sm">
                            {format(new Date(matchData.match_date), 'p')}
                        </p>
                    </div>

                    <div className="flex items-center justify-between">
                        {/* Home Team */}
                        <div className="flex flex-col items-center flex-1">
                            {matchData.home_team?.logo && (
                                <img
                                    src={matchData.home_team.logo}
                                    alt={matchData.home_team.name}
                                    className="w-24 h-24 object-contain mb-4"
                                />
                            )}
                            <h2 className="text-2xl font-bold text-white text-center">
                                {matchData.home_team?.name || 'TBD'}
                            </h2>
                            {matchData.home_goals !== null && (
                                <p className="text-4xl font-bold text-primary-400 mt-2">
                                    {matchData.home_goals}
                                </p>
                            )}
                        </div>

                        {/* VS */}
                        <div className="px-8">
                            <div className="text-4xl font-bold text-gray-600">VS</div>
                        </div>

                        {/* Away Team */}
                        <div className="flex flex-col items-center flex-1">
                            {matchData.away_team?.logo && (
                                <img
                                    src={matchData.away_team.logo}
                                    alt={matchData.away_team.name}
                                    className="w-24 h-24 object-contain mb-4"
                                />
                            )}
                            <h2 className="text-2xl font-bold text-white text-center">
                                {matchData.away_team?.name || 'TBD'}
                            </h2>
                            {matchData.away_goals !== null && (
                                <p className="text-4xl font-bold text-primary-400 mt-2">
                                    {matchData.away_goals}
                                </p>
                            )}
                        </div>
                    </div>

                    <div className="text-center mt-6">
                        <span className={`badge ${matchData.status === 'FT' ? 'badge-success' :
                            matchData.status === 'LIVE' ? 'badge-warning' :
                                'badge-info'
                            }`}>
                            {matchData.status === 'NS' ? 'Not Started' :
                                matchData.status === 'FT' ? 'Full Time' :
                                    matchData.status === 'LIVE' ? 'Live' :
                                        matchData.status}
                        </span>
                    </div>
                </div>
            )}

            {/* Prediction */}
            {predictionData ? (
                <div className="space-y-6">
                    {/* Main Prediction */}
                    <div className="card bg-gradient-to-br from-primary-600/20 to-primary-800/20 border-primary-500/30">
                        <h3 className="text-xl font-bold text-white mb-4">🎯 AI Prediction</h3>

                        <div className="text-center">
                            <p className="text-gray-400 text-sm mb-2">Predicted Winner</p>
                            <p className="text-4xl font-bold text-primary-400 capitalize mb-4">
                                {predictionData.predicted_result === 'H' ? matchData?.home_team?.name || 'Home' :
                                    predictionData.predicted_result === 'A' ? matchData?.away_team?.name || 'Away' :
                                        predictionData.predicted_result === 'D' ? 'Draw' :
                                            predictionData.predicted_result}
                            </p>

                            <div className="inline-flex items-center space-x-2 bg-dark-900/50 px-6 py-3 rounded-lg">
                                <span className="text-gray-400">Confidence:</span>
                                <span className="text-2xl font-bold text-white">
                                    {(predictionData.confidence * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>

                        {/* Exact Score Prediction */}
                        {predictionData.exact_score_prediction && (
                            <div className="mt-6 text-center">
                                <p className="text-gray-400 text-sm mb-2">Predicted Score</p>
                                <p className="text-3xl font-bold text-white">
                                    {predictionData.exact_score_prediction}
                                </p>
                                <p className="text-xs text-gray-500 mt-1">
                                    {((predictionData.exact_score_confidence || 0) * 100).toFixed(1)}% confidence
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Probabilities */}
                    <div className="card">
                        <h3 className="text-xl font-bold text-white mb-6">Win Probabilities</h3>

                        <div className="space-y-4">
                            {/* Home Win */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <span className="text-gray-400">Home Win</span>
                                    <span className="text-white font-semibold">
                                        {(predictionData.prob_home_win * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="w-full bg-dark-700 rounded-full h-3">
                                    <div
                                        className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500"
                                        style={{ width: `${predictionData.prob_home_win * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Draw */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <span className="text-gray-400">Draw</span>
                                    <span className="text-white font-semibold">
                                        {(predictionData.prob_draw * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="w-full bg-dark-700 rounded-full h-3">
                                    <div
                                        className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-3 rounded-full transition-all duration-500"
                                        style={{ width: `${predictionData.prob_draw * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Away Win */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <span className="text-gray-400">Away Win</span>
                                    <span className="text-white font-semibold">
                                        {(predictionData.prob_away_win * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="w-full bg-dark-700 rounded-full h-3">
                                    <div
                                        className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500"
                                        style={{ width: `${predictionData.prob_away_win * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Extended Predictions - BTTS, Over/Under, Multi-goal */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* BTTS (Both Teams To Score) */}
                        {predictionData.btts_prediction !== null && predictionData.btts_prediction !== undefined && (
                            <div className="card bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30">
                                <h3 className="text-lg font-bold text-white mb-4">⚽ Both Teams To Score</h3>
                                <div className="text-center">
                                    <p className={`text-3xl font-bold ${predictionData.btts_prediction ? 'text-green-400' : 'text-red-400'}`}>
                                        {predictionData.btts_prediction ? 'YES' : 'NO'}
                                    </p>
                                    <p className="text-gray-400 text-sm mt-2">
                                        {((predictionData.btts_confidence || 0) * 100).toFixed(1)}% confidence
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Over/Under 2.5 Goals */}
                        {predictionData.over_25_prediction !== null && predictionData.over_25_prediction !== undefined && (
                            <div className="card bg-gradient-to-br from-purple-600/20 to-purple-800/20 border-purple-500/30">
                                <h3 className="text-lg font-bold text-white mb-4">📊 Over/Under 2.5 Goals</h3>
                                <div className="text-center">
                                    <p className={`text-3xl font-bold ${predictionData.over_25_prediction ? 'text-green-400' : 'text-yellow-400'}`}>
                                        {predictionData.over_25_prediction ? 'OVER 2.5' : 'UNDER 2.5'}
                                    </p>
                                    <p className="text-gray-400 text-sm mt-2">
                                        {((predictionData.over_25_confidence || 0) * 100).toFixed(1)}% confidence
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Multi-goal Range */}
                        {predictionData.multi_goal_prediction && (
                            <div className="card bg-gradient-to-br from-orange-600/20 to-orange-800/20 border-orange-500/30">
                                <h3 className="text-lg font-bold text-white mb-4">🎯 Total Goals Range</h3>
                                <div className="text-center">
                                    <p className="text-3xl font-bold text-orange-400">
                                        {predictionData.multi_goal_prediction} Goals
                                    </p>
                                    <p className="text-gray-400 text-sm mt-2">
                                        {((predictionData.multi_goal_confidence || 0) * 100).toFixed(1)}% confidence
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Over 1.5 / Over 3.5 */}
                        {(predictionData.over_15_prediction !== null || predictionData.over_35_prediction !== null) && (
                            <div className="card">
                                <h3 className="text-lg font-bold text-white mb-4">📈 More Goals Markets</h3>
                                <div className="space-y-3">
                                    {predictionData.over_15_prediction !== null && (
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-400">Over 1.5 Goals</span>
                                            <span className={`font-bold ${predictionData.over_15_prediction ? 'text-green-400' : 'text-red-400'}`}>
                                                {predictionData.over_15_prediction ? '✓ YES' : '✗ NO'}
                                            </span>
                                        </div>
                                    )}
                                    {predictionData.over_35_prediction !== null && (
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-400">Over 3.5 Goals</span>
                                            <span className={`font-bold ${predictionData.over_35_prediction ? 'text-green-400' : 'text-red-400'}`}>
                                                {predictionData.over_35_prediction ? '✓ YES' : '✗ NO'}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Key Factors */}
                    {predictionData.key_factors && predictionData.key_factors.length > 0 && (
                        <div className="card">
                            <h3 className="text-xl font-bold text-white mb-4">Key Factors</h3>
                            <ul className="space-y-3">
                                {predictionData.key_factors.map((factor, index) => (
                                    <li key={index} className="flex items-start space-x-3">
                                        <span className="text-primary-500 mt-1">•</span>
                                        <span className="text-gray-300">{factor}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Model Info */}
                    <div className="card bg-dark-700/50">
                        <div className="flex items-center justify-between text-sm">
                            <div>
                                <span className="text-gray-400">Model:</span>
                                <span className="text-white ml-2 font-medium">
                                    {predictionData.model_type || 'ML Model'}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-400">Version:</span>
                                <span className="text-white ml-2 font-medium">
                                    {predictionData.model_version}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-400">Generated:</span>
                                <span className="text-white ml-2 font-medium">
                                    {format(new Date(predictionData.created_at), 'PPp')}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="card text-center py-12">
                    <div className="text-6xl mb-4">🤖</div>
                    <h3 className="text-xl font-bold text-white mb-2">No Prediction Available</h3>
                    <p className="text-gray-400">
                        {error ? 'Prediction has not been generated for this match yet.' : 'Loading...'}
                    </p>
                </div>
            )}
        </div>
    )
}

export default MatchPrediction
