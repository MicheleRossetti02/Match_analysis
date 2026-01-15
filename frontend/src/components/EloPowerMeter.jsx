import React from 'react'

/**
 * EloPowerMeter Component
 * 
 * Visualizes the ELO rating difference between home and away teams
 * using a centered power meter bar.
 * 
 * @param {number} eloDiff - The ELO difference (positive = home advantage, negative = away advantage)
 * @param {string} homeTeamName - Name of the home team
 * @param {string} awayTeamName - Name of the away team
 */
function EloPowerMeter({ eloDiff, homeTeamName, awayTeamName }) {
    // Calculate bar position: 50% = equilibrium, formula: 50 + (elo_diff / 10)
    // This means a +100 ELO advantage = 60% bar, -100 ELO = 40% bar
    const barPosition = 50 + (eloDiff / 10)

    // Clamp to 0-100 range for safety
    const clampedPosition = Math.max(0, Math.min(100, barPosition))

    // Determine which team has the advantage
    const homeAdvantage = eloDiff > 0
    const awayAdvantage = eloDiff < 0
    const balanced = eloDiff === 0

    return (
        <div className="card bg-gradient-to-br from-indigo-600/20 to-indigo-800/20 border-indigo-500/30">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">⚡ ELO Advantage</h3>
                <div className="flex items-center space-x-2">
                    <span className="text-gray-400 text-sm">ELO Diff:</span>
                    <span className={`text-lg font-bold ${homeAdvantage ? 'text-green-400' :
                            awayAdvantage ? 'text-red-400' :
                                'text-yellow-400'
                        }`}>
                        {eloDiff > 0 ? '+' : ''}{eloDiff.toFixed(0)}
                    </span>
                </div>
            </div>

            {/* Team Labels */}
            <div className="flex items-center justify-between mb-2 text-sm">
                <span className="text-gray-400 font-medium">
                    {awayTeamName || 'Away'}
                </span>
                <span className="text-gray-500 text-xs">
                    {balanced ? 'Equilibrium' : homeAdvantage ? 'Home Advantage' : 'Away Advantage'}
                </span>
                <span className="text-gray-400 font-medium">
                    {homeTeamName || 'Home'}
                </span>
            </div>

            {/* Power Meter Bar */}
            <div className="relative w-full h-10 bg-dark-900 rounded-lg overflow-hidden">
                {/* Center line indicator (50% equilibrium) */}
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-600 z-10"></div>

                {/* Animated gradient bar */}
                <div
                    className="absolute top-0 bottom-0 left-0 bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-700 ease-out"
                    style={{ width: `${clampedPosition}%` }}
                >
                    {/* Glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
                </div>

                {/* Percentage indicators */}
                <div className="absolute inset-0 flex items-center justify-between px-3 text-xs font-semibold z-20">
                    <span className={clampedPosition < 30 ? 'text-white' : 'text-gray-600'}>0%</span>
                    <span className={clampedPosition > 40 && clampedPosition < 60 ? 'text-white' : 'text-gray-600'}>50%</span>
                    <span className={clampedPosition > 70 ? 'text-white' : 'text-gray-600'}>100%</span>
                </div>
            </div>

            {/* Explanation */}
            <p className="text-xs text-gray-500 mt-3 text-center">
                ELO rating system measures team strength based on historical performance
            </p>
        </div>
    )
}

export default EloPowerMeter
