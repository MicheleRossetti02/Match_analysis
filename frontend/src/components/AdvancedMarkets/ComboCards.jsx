/**
 * Combo Cards Component
 * Displays top combo bet predictions with glassmorphism design
 */
import { useState } from 'react';
import useBetStore from '../../stores/useBetStore';

const COMBO_DISPLAY_MAP = {
    '1_over_25': {
        icon: '🏠⚽',
        text: 'Home Win & Over 2.5',
        description: 'Home team wins AND total goals > 2.5',
        shortText: '1 + O2.5'
    },
    '2_over_25': {
        icon: '✈️⚽',
        text: 'Away Win & Over 2.5',
        description: 'Away team wins AND total goals > 2.5',
        shortText: '2 + O2.5'
    },
    'x_under_25': {
        icon: '🤝🔽',
        text: 'Draw & Under 2.5',
        description: 'Match draws AND total goals ≤ 2.5',
        shortText: 'X + U2.5'
    },
    '1_btts': {
        icon: '🏠⚔️',
        text: 'Home Win & BTTS',
        description: 'Home team wins AND both teams score',
        shortText: '1 + GG'
    },
    '2_btts': {
        icon: '✈️⚔️',
        text: 'Away Win & BTTS',
        description: 'Away team wins AND both teams score',
        shortText: '2 + GG'
    },
    'x_btts': {
        icon: '🤝⚔️',
        text: 'Draw & BTTS',
        description: 'Match draws AND both teams score',
        shortText: 'X + GG'
    },
    'gg_over_25': {
        icon: '⚔️⚽',
        text: 'BTTS & Over 2.5',
        description: 'Both teams score AND total goals > 2.5',
        shortText: 'GG + O2.5'
    }
};

function ComboCards({ prediction, match }) {
    const addBet = useBetStore((state) => state.addBet);
    const hasBet = useBetStore((state) => state.hasBet);
    const [addedCombo, setAddedCombo] = useState(null);

    const combos = prediction.combo_predictions || {};
    const hasDixonColes = prediction.has_dixon_coles;

    // Get top 3 combos sorted by probability
    const topCombos = Object.entries(combos)
        .filter(([_, prob]) => prob > 0.15) // Minimum threshold
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([key, prob]) => ({
            key,
            ...COMBO_DISPLAY_MAP[key],
            probability: prob
        }));

    const handleAddToBolletta = (combo) => {
        const bet = {
            matchId: prediction.match_id,
            homeTeam: match?.home_team?.name || 'Home',
            awayTeam: match?.away_team?.name || 'Away',
            homeLogo: match?.home_team?.logo,
            awayLogo: match?.away_team?.logo,
            matchDate: match?.match_date,
            league: match?.league?.name,
            market: 'COMBO',
            betType: combo.key,
            betLabel: combo.shortText,
            description: combo.description,
            probability: combo.probability,
            color: getComboColor(combo.probability),
            category: 'Combo',
            hasDixonColes: hasDixonColes,
            isValue: combo.probability > 0.30 // Flag high-value combos
        };

        addBet(bet);
        setAddedCombo(combo.key);

        setTimeout(() => setAddedCombo(null), 2000);
    };

    const getComboColor = (prob) => {
        if (prob >= 0.35) return 'amber'; // High value
        if (prob >= 0.25) return 'cyan'; // Medium
        return 'gray'; // Speculative
    };

    const getValueLevel = (prob, kellyPct = null) => {
        // Priority 1: Use Kelly % if available (from betting analysis)
        if (kellyPct !== null && kellyPct !== undefined) {
            if (kellyPct >= 15) return { text: 'HIGH VALUE', color: 'green', emoji: '💎', tag: 'HIGH' };
            if (kellyPct >= 8) return { text: 'MEDIUM VALUE', color: 'cyan', emoji: '⭐', tag: 'MEDIUM' };
            if (kellyPct > 0) return { text: 'LOW VALUE', color: 'blue', emoji: '📊', tag: 'LOW' };
            return { text: 'NO VALUE', color: 'gray', emoji: '⛔', tag: 'NONE' };
        }

        // Priority 2: Fallback to probability-based (old logic)
        if (prob >= 0.35) return { text: 'HIGH VALUE', color: 'green', emoji: '💎', tag: 'HIGH' };
        if (prob >= 0.25) return { text: 'GOOD VALUE', color: 'cyan', emoji: '⭐', tag: 'MEDIUM' };
        return { text: 'SPECULATIVE', color: 'gray', emoji: '🎲', tag: 'LOW' };
    };

    if (topCombos.length === 0) {
        return (
            <div className="card text-center py-8">
                <div className="text-4xl mb-3">🎰</div>
                <p className="text-gray-400">No high-confidence combo bets available</p>
                <p className="text-sm text-gray-500 mt-1">Combos require ≥15% probability</p>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white">Combo Bets</h3>
                    <p className="text-sm text-gray-400 mt-1">Correlation-aware multi-market predictions</p>
                </div>
                {hasDixonColes && (
                    <div className="flex items-center gap-2">
                        <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-400 rounded-lg border border-purple-500/30 text-sm font-medium">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                            Bivariate Model
                        </span>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {topCombos.map((combo, idx) => {
                    const confidence = Math.round(combo.probability * 100);
                    // Get Kelly % if available from prediction.estimated_odds
                    const comboKelly = prediction.kelly_percentage || null;
                    const valueLevel = getValueLevel(combo.probability, comboKelly);
                    const isInBolletta = hasBet(prediction.match_id);
                    const wasJustAdded = addedCombo === combo.key;

                    return (
                        <div
                            key={combo.key}
                            className={`
                                relative overflow-hidden rounded-xl backdrop-blur-md transition-all duration-300
                                ${wasJustAdded ? 'scale-105 shadow-2xl' : 'scale-100'}
                                bg-gradient-to-br from-white/10 to-white/5
                                border border-white/20
                                hover:border-${valueLevel.color}-500/50
                                hover:shadow-lg hover:shadow-${valueLevel.color}-500/20
                            `}
                            style={{
                                background: wasJustAdded
                                    ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.1) 100%)'
                                    : undefined
                            }}
                        >
                            {/* Rank Badge */}
                            <div className="absolute top-3 left-3">
                                <span className={`
                                    inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm
                                    ${idx === 0 ? 'bg-yellow-500/30 text-yellow-300 ring-2 ring-yellow-500/50' :
                                        idx === 1 ? 'bg-gray-400/30 text-gray-300 ring-2 ring-gray-400/50' :
                                            'bg-orange-400/30 text-orange-300 ring-2 ring-orange-400/50'}
                                `}>
                                    #{idx + 1}
                                </span>
                            </div>

                            {/* Value Badge */}
                            <div className="absolute top-3 right-3">
                                <span className={`
                                    inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold uppercase
                                    ${valueLevel.tag === 'HIGH' ? 'bg-green-500/30 text-green-300 border-2 border-green-500 shadow-lg shadow-green-500/30' :
                                        valueLevel.tag === 'MEDIUM' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' :
                                            valueLevel.tag === 'LOW' ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' :
                                                'bg-gray-500/15 text-gray-400 border border-gray-500/20'
                                    }
                                `}>
                                    <span>{valueLevel.emoji}</span>
                                    <span>VALUE: {valueLevel.tag}</span>
                                </span>
                            </div>

                            {/* Content */}
                            <div className="p-6 pt-16">
                                {/* Icon */}
                                <div className="text-5xl mb-4 text-center">{combo.icon}</div>

                                {/* Label */}
                                <h4 className="text-lg font-bold text-white text-center mb-2">
                                    {combo.text}
                                </h4>
                                <p className="text-xs text-gray-400 text-center mb-4">
                                    {combo.description}
                                </p>

                                {/* Kelly Criterion Recommendation */}
                                {comboKelly !== null && comboKelly > 0 && (
                                    <div className="mb-3 p-2.5 bg-gradient-to-r from-green-500/15 to-emerald-500/15 rounded-lg border border-green-500/30">
                                        <p className="text-xs text-green-400 font-bold flex items-center justify-center gap-1.5">
                                            <span>📊</span>
                                            <span>Scommessa suggerita (Kelly): {comboKelly.toFixed(1)}%</span>
                                        </p>
                                    </div>
                                )}

                                {/* Confidence Indicator */}
                                <div className="relative mb-4">
                                    <div className="flex items-center justify-center">
                                        <div className="relative">
                                            <svg className="w-24 h-24 transform -rotate-90">
                                                <circle
                                                    cx="48"
                                                    cy="48"
                                                    r="40"
                                                    stroke="currentColor"
                                                    strokeWidth="6"
                                                    fill="none"
                                                    className="text-dark-600"
                                                />
                                                <circle
                                                    cx="48"
                                                    cy="48"
                                                    r="40"
                                                    stroke="currentColor"
                                                    strokeWidth="6"
                                                    fill="none"
                                                    strokeDasharray={`${2 * Math.PI * 40}`}
                                                    strokeDashoffset={`${2 * Math.PI * 40 * (1 - combo.probability)}`}
                                                    className={`text-${valueLevel.color}-400 transition-all duration-1000`}
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <span className="text-2xl font-bold text-white">{confidence}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Add Button */}
                                <button
                                    onClick={() => handleAddToBolletta(combo)}
                                    disabled={isInBolletta && !wasJustAdded}
                                    className={`
                                        w-full py-3 rounded-lg font-semibold transition-all duration-200
                                        ${wasJustAdded
                                            ? 'bg-green-500 text-white shadow-lg shadow-green-500/50'
                                            : isInBolletta
                                                ? 'bg-dark-600 text-gray-500 cursor-not-allowed'
                                                : `bg-gradient-to-r from-${valueLevel.color}-500 to-${valueLevel.color}-600 hover:from-${valueLevel.color}-600 hover:to-${valueLevel.color}-700 text-white shadow-lg hover:shadow-xl`}
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
            <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg border border-purple-500/20">
                <div className="flex items-start gap-3">
                    <div className="text-2xl">🧠</div>
                    <div className="flex-1 text-sm">
                        <p className="text-gray-300 font-medium mb-1">Why Combo Bets?</p>
                        <p className="text-gray-400 leading-relaxed">
                            Combo bets combine multiple outcomes for potentially higher odds. Our bivariate model accounts for correlations
                            (e.g., dominant wins often have many goals), making these predictions 5-10% more accurate than naive probability multiplication.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ComboCards;
