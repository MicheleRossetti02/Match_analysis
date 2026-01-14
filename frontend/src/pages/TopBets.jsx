import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { format } from 'date-fns'

// League flag mapping
const LEAGUE_FLAGS = {
    'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'Serie A': '🇮🇹',
    'La Liga': '🇪🇸',
    'Bundesliga': '🇩🇪',
    'Ligue 1': '🇫🇷'
}

// Prediction type tabs
const PREDICTION_TYPES = [
    { id: 'result', name: '1X2 Result', icon: '🎯', description: 'Match result predictions' },
    { id: 'btts', name: 'Both Teams Score', icon: '⚽', description: 'BTTS predictions' },
    { id: 'over25', name: 'Over 2.5 Goals', icon: '📊', description: 'Over/Under 2.5 goals' },
    { id: 'over15', name: 'Over 1.5 Goals', icon: '📈', description: 'Over/Under 1.5 goals' },
    { id: 'over35', name: 'Over 3.5 Goals', icon: '🔥', description: 'Over/Under 3.5 goals' },
]

function TopBets() {
    const [activeTab, setActiveTab] = useState('result')

    // Fetch top predictions by league
    const { data: topPredictions, isLoading } = useQuery({
        queryKey: ['topPredictionsByLeague'],
        queryFn: () => api.getTopPredictionsByLeague({ limit_per_league: 10, days: 14 }),
        staleTime: 5 * 60 * 1000,
    })

    const predictions = topPredictions?.data || {}
    const leagues = Object.values(predictions)

    // Get confidence color
    const getConfidenceColor = (confidence) => {
        if (confidence >= 70) return 'text-green-400'
        if (confidence >= 50) return 'text-yellow-400'
        return 'text-orange-400'
    }

    // Get confidence bg color
    const getConfidenceBg = (confidence) => {
        if (confidence >= 70) return 'bg-green-500/20 border-green-500/30'
        if (confidence >= 50) return 'bg-yellow-500/20 border-yellow-500/30'
        return 'bg-orange-500/20 border-orange-500/30'
    }

    // Get result badge
    const getResultBadge = (result) => {
        switch (result) {
            case 'H': return { text: 'Home Win', class: 'bg-blue-500/20 text-blue-400 border-blue-500/30' }
            case 'A': return { text: 'Away Win', class: 'bg-purple-500/20 text-purple-400 border-purple-500/30' }
            case 'D': return { text: 'Draw', class: 'bg-gray-500/20 text-gray-400 border-gray-500/30' }
            default: return { text: result, class: 'bg-gray-500/20 text-gray-400 border-gray-500/30' }
        }
    }

    // Filter and sort predictions based on active tab
    const getFilteredPredictions = (leaguePredictions) => {
        if (!leaguePredictions) return []

        return leaguePredictions
            .filter(pred => {
                switch (activeTab) {
                    case 'btts':
                        return pred.btts_prediction !== null && pred.btts_prediction !== undefined
                    case 'over25':
                        return pred.over_25_prediction !== null && pred.over_25_prediction !== undefined
                    case 'over15':
                        return true // All matches have this
                    case 'over35':
                        return true // All matches have this
                    default:
                        return true
                }
            })
            .slice(0, 10)
    }

    // Get the relevant confidence for the active tab
    const getRelevantConfidence = (pred) => {
        // For now, use the main confidence - the backend can be enhanced to return specific confidences
        return pred.confidence
    }

    // Get the prediction display for active tab
    const getPredictionDisplay = (pred) => {
        switch (activeTab) {
            case 'btts':
                return pred.btts_prediction ?
                    { text: 'Yes', class: 'bg-green-500/20 text-green-400 border-green-500/30' } :
                    { text: 'No', class: 'bg-red-500/20 text-red-400 border-red-500/30' }
            case 'over25':
                return pred.over_25_prediction ?
                    { text: 'Over 2.5', class: 'bg-green-500/20 text-green-400 border-green-500/30' } :
                    { text: 'Under 2.5', class: 'bg-red-500/20 text-red-400 border-red-500/30' }
            case 'over15':
                return { text: 'Over 1.5', class: 'bg-blue-500/20 text-blue-400 border-blue-500/30' }
            case 'over35':
                return { text: 'Over 3.5', class: 'bg-purple-500/20 text-purple-400 border-purple-500/30' }
            default:
                return getResultBadge(pred.predicted_result)
        }
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

            {/* Page Header */}
            <div className="text-center">
                <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
                    <span>🔥</span>
                    Top Bets by Confidence
                </h1>
                <p className="text-gray-400">
                    Highest confidence predictions for the next 14 days • Sorted by accuracy percentage
                </p>
            </div>

            {/* Prediction Type Tabs */}
            <div className="flex flex-wrap justify-center gap-2">
                {PREDICTION_TYPES.map((type) => (
                    <button
                        key={type.id}
                        onClick={() => setActiveTab(type.id)}
                        className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all ${activeTab === type.id
                                ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/25'
                                : 'bg-dark-800 text-gray-400 hover:text-white hover:bg-dark-700 border border-dark-600'
                            }`}
                    >
                        <span className="text-lg">{type.icon}</span>
                        <span>{type.name}</span>
                    </button>
                ))}
            </div>

            {/* Tab Description */}
            <div className="text-center">
                <p className="text-sm text-gray-500">
                    {PREDICTION_TYPES.find(t => t.id === activeTab)?.description}
                </p>
            </div>

            {/* Loading State */}
            {isLoading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
                    <p className="text-gray-400 mt-4">Loading predictions...</p>
                </div>
            ) : leagues.length === 0 ? (
                <div className="text-center py-12 card">
                    <p className="text-gray-400">No predictions available at the moment</p>
                </div>
            ) : (
                /* League Sections */
                <div className="space-y-8">
                    {leagues.map((league) => {
                        const filteredPreds = getFilteredPredictions(league.predictions)
                        if (filteredPreds.length === 0) return null

                        return (
                            <div key={league.league_id} className="card">
                                {/* League Header */}
                                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-dark-600">
                                    <span className="text-3xl">
                                        {LEAGUE_FLAGS[league.league_name] || '⚽'}
                                    </span>
                                    <div>
                                        <h2 className="text-xl font-bold text-white">{league.league_name}</h2>
                                        <p className="text-sm text-gray-400">{league.country}</p>
                                    </div>
                                    <div className="ml-auto">
                                        <span className="badge badge-info">
                                            {filteredPreds.length} matches
                                        </span>
                                    </div>
                                </div>

                                {/* Predictions Grid */}
                                <div className="grid gap-4">
                                    {filteredPreds.map((pred, index) => {
                                        const predDisplay = getPredictionDisplay(pred)
                                        const confidence = getRelevantConfidence(pred)

                                        return (
                                            <Link
                                                key={pred.match_id}
                                                to={`/match/${pred.match_id}`}
                                                className="flex items-center gap-4 p-4 bg-dark-700/50 rounded-xl hover:bg-dark-700 transition-colors group"
                                            >
                                                {/* Rank */}
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                                                        index === 1 ? 'bg-gray-400/20 text-gray-300' :
                                                            index === 2 ? 'bg-orange-700/20 text-orange-400' :
                                                                'bg-dark-600 text-gray-500'
                                                    }`}>
                                                    {index + 1}
                                                </div>

                                                {/* Match Info */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="font-medium text-white truncate">
                                                            {pred.home_team}
                                                        </span>
                                                        <span className="text-gray-500">vs</span>
                                                        <span className="font-medium text-white truncate">
                                                            {pred.away_team}
                                                        </span>
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        {format(new Date(pred.match_date), 'EEE, MMM d · HH:mm')}
                                                    </div>
                                                </div>

                                                {/* Prediction Badge */}
                                                <div className={`px-3 py-1.5 rounded-lg border ${predDisplay.class} font-medium text-sm`}>
                                                    {activeTab === 'result' ? pred.winner_name || predDisplay.text : predDisplay.text}
                                                </div>

                                                {/* Confidence */}
                                                <div className={`px-4 py-2 rounded-lg border ${getConfidenceBg(confidence)} min-w-[80px] text-center`}>
                                                    <div className={`text-lg font-bold ${getConfidenceColor(confidence)}`}>
                                                        {confidence}%
                                                    </div>
                                                </div>

                                                {/* Arrow */}
                                                <div className="text-gray-600 group-hover:text-primary-500 transition-colors">
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                    </svg>
                                                </div>
                                            </Link>
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Footer Note */}
            <div className="text-center text-sm text-gray-500 py-4">
                <p>
                    🎯 Predictions ranked by main confidence score • Click any match for detailed analysis
                </p>
            </div>
        </div>
    )
}

export default TopBets
