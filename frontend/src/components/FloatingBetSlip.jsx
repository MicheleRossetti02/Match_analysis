import React, { useState } from 'react';
import { useBetSlip } from '../context/BetSlipContext';
import { X, Trash2, Calculator } from 'lucide-react';

const FloatingBetSlip = () => {
    const { selectedBets, removeBet, clearBetSlip, getTotalOdds, getPotentialProfit, updateBetMarket } = useBetSlip();
    const [isOpen, setIsOpen] = useState(true);
    const [stake, setStake] = useState(10);

    if (selectedBets.length === 0) {
        return null; // Don't show if empty
    }

    const totalOdds = getTotalOdds();
    const potentialWin = stake * totalOdds;
    const profit = getPotentialProfit(stake);

    // Estimate odds for each market
    const getEstimatedOdds = (prediction, market) => {
        const prob = market === '1' ? prediction.prob_home_win :
            market === 'X' ? prediction.prob_draw :
                prediction.prob_away_win;

        return prob > 0 ? (1 / prob).toFixed(2) : 1.00;
    };

    return (
        <div className={`fixed right-4 top-20 w-96 bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl shadow-2xl border border-gray-700 z-50 transition-transform ${isOpen ? 'translate-x-0' : 'translate-x-[420px]'}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <div className="flex items-center space-x-2">
                    <Calculator className="w-5 h-5 text-green-400" />
                    <h3 className="font-bold text-lg">Bolletta ({selectedBets.length})</h3>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="p-1 hover:bg-gray-700 rounded transition-colors"
                    >
                        {isOpen ? <X className="w-5 h-5" /> : '📋'}
                    </button>
                </div>
            </div>

            {isOpen && (
                <>
                    {/* Bets List */}
                    <div className="max-h-96 overflow-y-auto p-4 space-y-3">
                        {selectedBets.map((bet) => (
                            <div key={bet.match.id} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                        <div className="text-sm font-semibold">
                                            {bet.match.home_team?.name} vs {bet.match.away_team?.name}
                                        </div>
                                        <div className="text-xs text-gray-400 mt-1">
                                            {new Date(bet.match.match_date).toLocaleString('it-IT', {
                                                weekday: 'short',
                                                day: 'numeric',
                                                month: 'short',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => removeBet(bet.match.id)}
                                        className="p-1 hover:bg-red-500/20 rounded transition-colors"
                                    >
                                        <X className="w-4 h-4 text-red-400" />
                                    </button>
                                </div>

                                {/* Market Selection */}
                                <div className="grid grid-cols-3 gap-2">
                                    {['1', 'X', '2'].map(market => {
                                        const isSelected = bet.selectedMarket === market;
                                        const odds = getEstimatedOdds(bet.prediction, market);

                                        return (
                                            <button
                                                key={market}
                                                onClick={() => updateBetMarket(bet.match.id, market, parseFloat(odds))}
                                                className={`py-2 px-3 rounded-lg text-sm font-semibold transition-all ${isSelected
                                                        ? 'bg-green-500 text-white'
                                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                                    }`}
                                            >
                                                <div>{market}</div>
                                                <div className="text-xs opacity-90">{odds}</div>
                                            </button>
                                        );
                                    })}
                                </div>

                                {/* AI Confidence */}
                                <div className="mt-2 text-xs text-gray-400">
                                    AI: {bet.prediction.predicted_result === 'H' ? '1' :
                                        bet.prediction.predicted_result === 'D' ? 'X' : '2'}
                                    ({(bet.prediction.confidence * 100).toFixed(1)}% confidence)
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Summary */}
                    <div className="border-t border-gray-700 p-4 space-y-3">
                        {/* Stake Input */}
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Stake (€)</label>
                            <input
                                type="number"
                                value={stake}
                                onChange={(e) => setStake(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-green-500"
                                min="0"
                                step="5"
                            />
                        </div>

                        {/* Odds Summary */}
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-400">Quote totali:</span>
                                <span className="font-bold text-green-400">{totalOdds.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-400">Vincita potenziale:</span>
                                <span className="font-bold text-white">€{potentialWin.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Profitto:</span>
                                <span className="font-bold text-xl text-green-400">+€{profit.toFixed(2)}</span>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex space-x-2">
                            <button
                                onClick={clearBetSlip}
                                className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                            >
                                <Trash2 className="w-4 h-4" />
                                <span>Svuota</span>
                            </button>
                            <button
                                className="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all"
                            >
                                Piazza Scommessa
                            </button>
                        </div>
                    </div>
                </>
            )}

            {/* Toggle Button when closed */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="absolute -left-10 top-0 bg-green-500 text-white p-2 rounded-l-lg shadow-lg hover:bg-green-600 transition-colors"
                >
                    <div className="flex flex-col items-center">
                        <Calculator className="w-5 h-5" />
                        <span className="text-xs mt-1">{selectedBets.length}</span>
                    </div>
                </button>
            )}
        </div>
    );
};

export default FloatingBetSlip;
