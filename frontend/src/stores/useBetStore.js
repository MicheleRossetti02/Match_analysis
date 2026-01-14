/**
 * Zustand Store for Bolletta Management
 * 
 * Centralized state for bet selections with localStorage persistence
 * Provides actions for add/remove/clear bets across all pages
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useBetStore = create(
    persist(
        (set, get) => ({
            // ========== STATE ==========
            selectedBets: [],  // Array of bet objects
            bollettaVisible: false,

            // ========== ACTIONS ==========

            /**
             * Add or update a bet for a match
             * If match already exists, replaces with new bet
             */
            addBet: (bet) => {
                set((state) => {
                    // Remove existing bet for same match if exists
                    const filteredBets = state.selectedBets.filter(
                        (b) => b.matchId !== bet.matchId
                    );

                    return {
                        selectedBets: [...filteredBets, bet]
                    };
                });
            },

            /**
             * Remove bet by match ID
             */
            removeBet: (matchId) => {
                set((state) => ({
                    selectedBets: state.selectedBets.filter(
                        (b) => b.matchId !== matchId
                    )
                }));
            },

            /**
             * Clear all bets
             */
            clearBets: () => {
                set({ selectedBets: [] });
            },

            /**
             * Toggle bolletta visibility
             */
            toggleBolletta: () => {
                set((state) => ({
                    bollettaVisible: !state.bollettaVisible
                }));
            },

            /**
             * Show bolletta panel
             */
            showBolletta: () => {
                set({ bollettaVisible: true });
            },

            /**
             * Hide bolletta panel
             */
            hideBolletta: () => {
                set({ bollettaVisible: false });
            },

            // ========== SELECTORS ==========

            /**
             * Get total number of bets
             */
            getBetCount: () => {
                return get().selectedBets.length;
            },

            /**
             * Check if match is already in bolletta
             */
            hasBet: (matchId) => {
                return get().selectedBets.some((b) => b.matchId === matchId);
            },

            /**
             * Get bet for specific match
             */
            getBet: (matchId) => {
                return get().selectedBets.find((b) => b.matchId === matchId);
            },

            /**
             * Calculate combined probability
             */
            getCombinedProbability: () => {
                const bets = get().selectedBets;
                if (bets.length === 0) return 0;

                return bets.reduce((acc, bet) => acc * bet.probability, 1);
            },

            /**
             * Calculate implied odds
             */
            getImpliedOdds: () => {
                const combinedProb = get().getCombinedProbability();
                return combinedProb > 0 ? 1 / combinedProb : 0;
            },

            /**
             * Get bets grouped by league
             */
            getBetsByLeague: () => {
                const bets = get().selectedBets;
                const grouped = {};

                bets.forEach((bet) => {
                    const league = bet.league || 'Unknown';
                    if (!grouped[league]) {
                        grouped[league] = [];
                    }
                    grouped[league].push(bet);
                });

                return grouped;
            },

            /**
             * Get best bets (top N by probability)
             */
            getTopBets: (n = 10) => {
                return [...get().selectedBets]
                    .sort((a, b) => b.probability - a.probability)
                    .slice(0, n);
            }
        }),
        {
            name: 'match-analysis-bolletta', // localStorage key
            partialPersist: true,
            // Only persist selectedBets, not UI state
            partialize: (state) => ({
                selectedBets: state.selectedBets
            })
        }
    )
);

export default useBetStore;
