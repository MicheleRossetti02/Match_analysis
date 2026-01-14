import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { format } from 'date-fns'

function Leagues() {
    const { leagueId } = useParams()

    // Fetch league matches
    const { data: matches, isLoading } = useQuery({
        queryKey: ['leagueMatches', leagueId],
        queryFn: () => api.getLeagueMatches(leagueId, { limit: 50, status: 'NS' }),
    })

    // Fetch teams for this league
    const { data: teams } = useQuery({
        queryKey: ['leagueTeams', leagueId],
        queryFn: () => api.getLeagueTeams(leagueId),
    })

    if (isLoading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                <p className="text-gray-400 mt-4">Loading matches...</p>
            </div>
        )
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
            <div>
                <h1 className="text-4xl font-bold text-white">League Matches</h1>
                <p className="text-gray-400 mt-2">Upcoming matches and predictions</p>
            </div>

            {/* Matches List */}
            <div className="space-y-3">
                {matches?.data && matches.data.length > 0 ? (
                    matches.data.map((match) => (
                        <Link
                            key={match.id}
                            to={`/match/${match.id}`}
                            className="block card hover:border-primary-500/50 transition-all group overflow-hidden"
                        >
                            {/* Date Header */}
                            <div className="flex items-center justify-between mb-4 pb-3 border-b border-dark-700">
                                <div className="flex items-center gap-3">
                                    <span className="text-primary-400 font-medium">
                                        📅 {format(new Date(match.match_date), 'EEEE, MMM d, yyyy')}
                                    </span>
                                    <span className="text-gray-500">•</span>
                                    <span className="text-gray-400">
                                        {format(new Date(match.match_date), 'h:mm a')}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    {match.round && (
                                        <span className="text-xs text-gray-500 bg-dark-700 px-2 py-1 rounded">
                                            {match.round}
                                        </span>
                                    )}
                                    <span className="badge badge-info">{match.status}</span>
                                </div>
                            </div>

                            {/* Teams Row */}
                            <div className="flex items-center justify-between">
                                {/* Home Team */}
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    {match.home_team?.logo ? (
                                        <img
                                            src={match.home_team.logo}
                                            alt={match.home_team.name}
                                            className="w-12 h-12 object-contain flex-shrink-0"
                                        />
                                    ) : (
                                        <div className="w-12 h-12 bg-dark-700 rounded-full flex items-center justify-center flex-shrink-0">
                                            <span className="text-xl">⚽</span>
                                        </div>
                                    )}
                                    <span className="font-semibold text-white text-lg truncate">
                                        {match.home_team?.name || 'TBD'}
                                    </span>
                                </div>

                                {/* VS Badge */}
                                <div className="px-5 py-2 bg-dark-700 rounded-lg mx-4 flex-shrink-0">
                                    <span className="text-gray-400 font-bold">VS</span>
                                </div>

                                {/* Away Team */}
                                <div className="flex items-center gap-3 flex-1 min-w-0 justify-end">
                                    <span className="font-semibold text-white text-lg truncate text-right">
                                        {match.away_team?.name || 'TBD'}
                                    </span>
                                    {match.away_team?.logo ? (
                                        <img
                                            src={match.away_team.logo}
                                            alt={match.away_team.name}
                                            className="w-12 h-12 object-contain flex-shrink-0"
                                        />
                                    ) : (
                                        <div className="w-12 h-12 bg-dark-700 rounded-full flex items-center justify-center flex-shrink-0">
                                            <span className="text-xl">⚽</span>
                                        </div>
                                    )}
                                </div>

                                {/* Arrow */}
                                <div className="text-gray-600 group-hover:text-primary-500 transition-colors ml-4 flex-shrink-0">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        </Link>
                    ))
                ) : (
                    <div className="card text-center py-12">
                        <div className="text-6xl mb-4">📅</div>
                        <h3 className="text-xl font-bold text-white mb-2">No Upcoming Matches</h3>
                        <p className="text-gray-400">
                            Check back later for upcoming fixtures and predictions.
                        </p>
                    </div>
                )}
            </div>

            {/* Teams Section */}
            {teams?.data && teams.data.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-2xl font-bold text-white">Teams</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {teams.data.map((team) => (
                            <div key={team.id} className="card text-center">
                                {team.logo && (
                                    <img
                                        src={team.logo}
                                        alt={team.name}
                                        className="w-16 h-16 object-contain mx-auto mb-3"
                                    />
                                )}
                                <p className="font-medium text-white">{team.name}</p>
                                {team.code && (
                                    <p className="text-xs text-gray-500 mt-1">{team.code}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Leagues
