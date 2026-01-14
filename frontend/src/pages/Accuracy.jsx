import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

function Accuracy() {
    // Fetch overall accuracy stats
    const { data: overallStats, isLoading: loadingOverall } = useQuery({
        queryKey: ['accuracyOverall'],
        queryFn: () => api.getAccuracyOverall(),
    })

    // Fetch accuracy by bet type
    const { data: betTypeStats, isLoading: loadingBetType } = useQuery({
        queryKey: ['accuracyByBetType'],
        queryFn: () => api.getAccuracyByBetType(),
    })

    // Fetch accuracy history
    const { data: historyStats, isLoading: loadingHistory } = useQuery({
        queryKey: ['accuracyHistory'],
        queryFn: () => api.getAccuracyHistory({ period: 'week', limit: 8 }),
    })

    //  Fetch recent predictions with results
    const { data: recentPredictions, isLoading: loadingRecent } = useQuery({
        queryKey: ['predictionsWithResults'],
        queryFn: () => api.getPredictionsWithResults({ limit: 20 }),
    })

    const stats = overallStats?.data?.data || {}
    const betTypes = betTypeStats?.data?.data || {}
    const history = historyStats?.data?.data || []
    const predictions = recentPredictions?.data?.data || []

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center space-y-4">
                <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-400 to-blue-500 bg-clip-text text-transparent">
                    Prediction Accuracy
                </h1>
                <p className="text-gray-400 text-lg">
                    Track model performance across all bet types
                </p>
            </div>

            {/* Overall Stats */}
            {loadingOverall ? (
                <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="card bg-gradient-to-br from-primary-600/20 to-primary-800/20 border-primary-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Total Predictions</h3>
                        <p className="text-4xl font-bold text-primary-400 mt-2">
                            {stats.total_predictions || 0}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">Predictions evaluated</p>
                    </div>

                    <div className="card bg-gradient-to-br from-emerald-600/20 to-emerald-800/20 border-emerald-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">1X2 Accuracy</h3>
                        <p className="text-4xl font-bold text-emerald-400 mt-2">
                            {stats.accuracy_1x2?.percentage || 0}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            {stats.accuracy_1x2?.correct || 0}/{stats.accuracy_1x2?.total || 0} correct
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">BTTS Accuracy</h3>
                        <p className="text-4xl font-bold text-blue-400 mt-2">
                            {stats.accuracy_btts?.percentage || 0}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            {stats.accuracy_btts?.correct || 0}/{stats.accuracy_btts?.total || 0} correct
                        </p>
                    </div>
                </div>
            )}

            {/* Bet Type Breakdown */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white">Accuracy by Bet Type</h2>

                {loadingBetType ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* 1X2 */}
                        <div className="card hover:border-primary-500/50 transition-all">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">1X2 - Match Result</h3>
                                    <p className="text-sm text-gray-400">Home / Draw / Away</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-primary-400">
                                        {betTypes['1x2']?.percentage || 0}%
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {betTypes['1x2']?.correct}/{betTypes['1x2']?.total}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* BTTS */}
                        <div className="card hover:border-blue-500/50 transition-all">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">BTTS</h3>
                                    <p className="text-sm text-gray-400">Both Teams To Score</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-blue-400">
                                        {betTypes.btts?.percentage || 0}%
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {betTypes.btts?.correct}/{betTypes.btts?.total}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Over 1.5 */}
                        <div className="card hover:border-purple-500/50 transition-all">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">Over/Under 1.5</h3>
                                    <p className="text-sm text-gray-400">Total Goals</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-purple-400">
                                        {betTypes.over_15?.percentage || 0}%
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {betTypes.over_15?.correct}/{betTypes.over_15?.total}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Over 2.5 */}
                        <div className="card hover:border-emerald-500/50 transition-all">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">Over/Under 2.5</h3>
                                    <p className="text-sm text-gray-400">Total Goals</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-emerald-400">
                                        {betTypes.over_25?.percentage || 0}%
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {betTypes.over_25?.correct}/{betTypes.over_25?.total}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Over 3.5 */}
                        <div className="card hover:border-amber-500/50 transition-all">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white">Over/Under 3.5</h3>
                                    <p className="text-sm text-gray-400">Total Goals</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-amber-400">
                                        {betTypes.over_35?.percentage || 0}%
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {betTypes.over_35?.correct}/{betTypes.over_35?.total}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Accuracy Trend Chart */}
            {history.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-2xl font-bold text-white">Accuracy Trend</h2>
                    <div className="card">
                        <div className="space-y-4">
                            {history.map((period, index) => (
                                <div key={index} className="flex items-center gap-4">
                                    <div className="w-32 text-sm text-gray-400 flex-shrink-0">
                                        {period.label}
                                    </div>
                                    <div className="flex-1">
                                        <div className="w-full bg-dark-700 rounded-full h-6 overflow-hidden">
                                            <div
                                                className={`h-full flex items-center justify-center text-xs font-bold transition-all ${period.accuracy >= 60
                                                        ? 'bg-emerald-500'
                                                        : period.accuracy >= 50
                                                            ? 'bg-yellow-500'
                                                            : 'bg-red-500'
                                                    }`}
                                                style={{ width: `${period.accuracy}%` }}
                                            >
                                                {period.accuracy}%
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-sm text-gray-400 w-24 text-right">
                                        {period.correct}/{period.total}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Recent Predictions with Results */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white">Recent Predictions</h2>

                {loadingRecent ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                    </div>
                ) : predictions.length > 0 ? (
                    <div className="card overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-dark-800 border-b border-dark-700">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            Match
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            League
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            Score
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            Prediction
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            Actual
                                        </th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                                            Result
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-dark-700">
                                    {predictions.map((pred) => (
                                        <tr key={pred.id} className="hover:bg-dark-800/50 transition-colors">
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    {pred.home_team_logo && (
                                                        <img
                                                            src={pred.home_team_logo}
                                                            alt=""
                                                            className="w-5 h-5 object-contain"
                                                        />
                                                    )}
                                                    <span className="text-white font-medium">
                                                        {pred.home_team}
                                                    </span>
                                                    <span className="text-gray-500">vs</span>
                                                    <span className="text-white font-medium">
                                                        {pred.away_team}
                                                    </span>
                                                    {pred.away_team_logo && (
                                                        <img
                                                            src={pred.away_team_logo}
                                                            alt=""
                                                            className="w-5 h-5 object-contain"
                                                        />
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-400">
                                                {pred.league}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="text-white font-bold">{pred.score}</span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="text-primary-400 font-medium">
                                                    {pred.prediction}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="text-white font-medium">
                                                    {pred.actual}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                {pred.is_correct ? (
                                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                                        ✓ Correct
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
                                                        ✗ Incorrect
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <div className="card text-center py-12">
                        <div className="text-4xl mb-3">📊</div>
                        <h3 className="text-lg font-bold text-white mb-1">No Results Yet</h3>
                        <p className="text-gray-400 text-sm">
                            Prediction results will appear here once matches are completed.
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Accuracy
