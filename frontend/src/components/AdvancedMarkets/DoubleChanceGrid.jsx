/**
 * Double Chance Grid Component
 * Displays 3 Double Chance options (1X, 12, X2) with probability bars
 */
import { useState } from 'react';
import useBetStore from '../../stores/useBetStore';

function DoubleChanceGrid({ prediction, match }) {
    const addBet = useBetStore((state) => state.addBet);
    const hasBet = useBetStore((state) => state.hasBet);
    const [addedOption, setAddedOption] = useState(null);

    const dc = prediction.double_chance || {};
    const hasDixonColes = prediction.has_dixon_coles;

    const dcOptions = [
        {
            key: '1X',
            label: '1X',
            description: 'Home or Draw',
            prob: dc['1X'] || 0,
            color: 'blue'
        },
        {
            key: '12',
            label: '12',
            description: 'Home or Away (No Draw)',
            prob: dc['12'] || 0,
            color: 'purple'
        },
        {
            key: 'X2',
            label: 'X2',
            description: 'Draw or Away',
            prob: dc['X2'] || 0,
            color: 'green'
        }
    ];

    const handleAddToBolletta = (option) => {
        const bet = {
            matchId: prediction.match_id,
            homeTeam: match?.home_team?.name || 'Home',
            awayTeam: match?.away_team?.name || 'Away',
            homeLogo: match?.home_team?.logo,
            awayLogo: match?.away_team?.logo,
            matchDate: match?.match_date,
            league: match?.league?.name,
            market: 'DC',
            betType: option.key,
            betLabel: `DC ${option.label}`,
            description: option.description,
            probability: option.prob,
            color: option.color,
            category: 'Double Chance',
            hasDixonColes: hasDixonColes
        };

        addBet(bet);
        setAddedOption(option.key);

        // Reset animation after 2s
        setTimeout(() => setAddedOption(null), 2000);
    };

    const getRiskLevel = (prob) => {
        if (prob > 0.75) return 'low';
        if (prob > 0.65) return 'medium';
        return 'high';
    };

    const getRiskColor = (risk) => {
        switch (risk) {
            case 'low': return 'emerald';
            case 'medium': return 'yellow';
            case 'high': return 'orange';
            default: return 'gray';
        }
    };

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white">Double Chance Markets</h3>
                    <p className="text-sm text-gray-400 mt-1">Higher win probability, lower odds</p>
                </div>
                {hasDixonColes && (
                    <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-500/20 text-primary-400 rounded-lg border border-primary-500/30 text-sm font-medium">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Dixon-Coles
                    </span>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {dcOptions.map((option) => {
                    const confidence = Math.round(option.prob * 100);
                    const riskLevel = getRiskLevel(option.prob);
                    const riskColor = getRiskColor(riskLevel);
                    const isInBolletta = hasBet(prediction.match_id);
                    const wasJustAdded = addedOption === option.key;

                    return (
                        <div
                            key={option.key}
                            className={`
                                relative overflow-hidden rounded-lg border-2 transition-all duration-300
                                ${wasJustAdded ? 'scale-105' : 'scale-100'}
                                ${riskLevel === 'low' ? 'border-emerald-500/50 bg-emerald-500/10' :
                                    riskLevel === 'medium' ? 'border-yellow-500/50 bg-yellow-500/10' :
                                        'border-orange-500/50 bg-orange-500/10'}
                            `}
                        >
                            {/* Header */}
                            <div className="p-4 border-b border-dark-600">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-2xl font-bold text-white">{option.label}</span>
                                    <span className={`
                                        text-xs font-semibold px-2 py-1 rounded
                                        ${riskLevel === 'low' ? 'bg-emerald-500/20 text-emerald-400' :
                                            riskLevel === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-orange-500/20 text-orange-400'}
                                    `}>
                                        {riskLevel} risk
                                    </span>
                                </div>
                                <p className="text-sm text-gray-400">{option.description}</p>
                            </div>

                            {/* Probability Bar */}
                            <div className="p-4">
                                <div className="mb-3">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-400">Probability</span>
                                        <span className="text-white font-bold">{confidence}%</span>
                                    </div>
                                    <div className="w-full bg-dark-700 rounded-full h-4 overflow-hidden">
                                        <div
                                            className={`
                                                h-4 rounded-full transition-all duration-500 flex items-center justify-end pr-2
                                                ${riskLevel === 'low' ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' :
                                                    riskLevel === 'medium' ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                                                        'bg-gradient-to-r from-orange-600 to-orange-400'}
                                            `}
                                            style={{ width: `${confidence}%` }}
                                        >
                                            <span className="text-xs font-bold text-white drop-shadow">
                                                {confidence > 30 && `${confidence}%`}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Add Button */}
                                <button
                                    onClick={() => handleAddToBolletta(option)}
                                    disabled={isInBolletta && !wasJustAdded}
                                    className={`
                                        w-full py-2.5 rounded-lg font-semibold text-sm transition-all duration-200
                                        ${wasJustAdded
                                            ? 'bg-green-500 text-white'
                                            : isInBolletta
                                                ? 'bg-dark-600 text-gray-500 cursor-not-allowed'
                                                : `bg-${riskColor}-500 hover:bg-${riskColor}-600 text-white`}
                                    `}
                                >
                                    {wasJustAdded ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                            Added!
                                        </span>
                                    ) : isInBolletta ? (
                                        'In Bolletta'
                                    ) : (
                                        'Add to Bolletta'
                                    )}
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Info Box */}
            <div className="mt-4 p-4 bg-dark-700/50 rounded-lg border border-dark-600">
                <div className="flex items-start gap-3">
                    <div className="text-2xl">ℹ️</div>
                    <div className="flex-1 text-sm">
                        <p className="text-gray-300 font-medium mb-1">About Double Chance</p>
                        <p className="text-gray-400 leading-relaxed">
                            Double Chance bets cover two of the three possible outcomes, offering higher win probability but typically lower odds than straight 1X2 bets.
                            {hasDixonColes && " These probabilities are correlation-adjusted using the Dixon-Coles bivariate model."}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DoubleChanceGrid;
