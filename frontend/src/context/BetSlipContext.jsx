import React, { createContext, useContext, useState, useEffect } from 'react';

const BetSlipContext = createContext();

export const useBetSlip = () => {
    const context = useContext(BetSlipContext);
    if (!context) {
        throw new Error('useBetSlip must be used within BetSlipProvider');
    }
    return context;
};

export const BetSlipProvider = ({ children }) => {
    const [selectedBets, setSelectedBets] = useState([]);

    // Load from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem('betSlip');
        if (saved) {
            try {
                setSelectedBets(JSON.parse(saved));
            } catch (e) {
                console.error('Error loading bet slip:', e);
            }
        }
    }, []);

    // Save to localStorage on change
    useEffect(() => {
        localStorage.setItem('betSlip', JSON.stringify(selectedBets));
    }, [selectedBets]);

    const addBet = (match, prediction, selectedMarket, odds) => {
        // Check if match already in slip
        const existingIndex = selectedBets.findIndex(bet => bet.match.id === match.id);

        if (existingIndex >= 0) {
            // Update existing bet
            const updated = [...selectedBets];
            updated[existingIndex] = {
                match,
                prediction,
                selectedMarket,
                odds,
                addedAt: new Date().toISOString()
            };
            setSelectedBets(updated);
        } else {
            // Add new bet
            setSelectedBets([...selectedBets, {
                match,
                prediction,
                selectedMarket,
                odds,
                addedAt: new Date().toISOString()
            }]);
        }
    };

    const removeBet = (matchId) => {
        setSelectedBets(selectedBets.filter(bet => bet.match.id !== matchId));
    };

    const clearBetSlip = () => {
        setSelectedBets([]);
    };

    const updateBetMarket = (matchId, newMarket, newOdds) => {
        setSelectedBets(selectedBets.map(bet =>
            bet.match.id === matchId
                ? { ...bet, selectedMarket: newMarket, odds: newOdds }
                : bet
        ));
    };

    // Calculate total odds (multiplier)
    const getTotalOdds = () => {
        if (selectedBets.length === 0) return 1.0;
        return selectedBets.reduce((total, bet) => total * bet.odds, 1.0);
    };

    // Calculate potential profit
    const getPotentialProfit = (stake) => {
        return (stake * getTotalOdds()) - stake;
    };

    const value = {
        selectedBets,
        addBet,
        removeBet,
        clearBetSlip,
        updateBetMarket,
        getTotalOdds,
        getPotentialProfit,
        betCount: selectedBets.length
    };

    return (
        <BetSlipContext.Provider value={value}>
            {children}
        </BetSlipContext.Provider>
    );
};
