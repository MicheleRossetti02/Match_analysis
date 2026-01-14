import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Leagues from './pages/Leagues'
import MatchPrediction from './pages/MatchPrediction'
import Statistics from './pages/Statistics'
import TopBets from './pages/TopBets'
import Bolletta from './pages/Bolletta'
import Accuracy from './pages/Accuracy'

function App() {
    return (
        <div className="min-h-screen bg-dark-900">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/leagues/:leagueId" element={<Leagues />} />
                    <Route path="/match/:matchId" element={<MatchPrediction />} />
                    <Route path="/statistics" element={<Statistics />} />
                    <Route path="/top-bets" element={<TopBets />} />
                    <Route path="/bolletta" element={<Bolletta />} />
                    <Route path="/accuracy" element={<Accuracy />} />
                </Routes>
            </main>
        </div>
    )
}

export default App

