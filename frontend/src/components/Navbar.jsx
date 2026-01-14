import { Link } from 'react-router-dom'

function Navbar() {
    return (
        <nav className="bg-dark-800 border-b border-dark-700 shadow-lg">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center space-x-3 group">
                        <div className="text-3xl transform group-hover:scale-110 transition-transform">⚽</div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Football Predictions</h1>
                            <p className="text-xs text-gray-400">ML-Powered Analysis</p>
                        </div>
                    </Link>

                    {/* Navigation Links */}
                    <div className="flex items-center space-x-6">
                        <Link
                            to="/"
                            className="text-gray-300 hover:text-white transition-colors font-medium"
                        >
                            Dashboard
                        </Link>

                        {/* Top Bets Link */}
                        <Link
                            to="/top-bets"
                            className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 hover:from-orange-500/20 hover:to-red-500/20 transition-all"
                        >
                            <span className="text-lg">🔥</span>
                            <span className="text-sm font-medium text-orange-400 hover:text-orange-300">
                                Top Bets
                            </span>
                        </Link>

                        {/* Bolletta Link */}
                        <Link
                            to="/bolletta"
                            className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 hover:from-emerald-500/20 hover:to-teal-500/20 transition-all"
                        >
                            <span className="text-lg">🎫</span>
                            <span className="text-sm font-medium text-emerald-400 hover:text-emerald-300">
                                Bolletta
                            </span>
                        </Link>

                        <Link
                            to="/accuracy"
                            className="text-gray-300 hover:text-white transition-colors font-medium"
                        >
                            Accuracy
                        </Link>

                        <Link
                            to="/statistics"
                            className="text-gray-300 hover:text-white transition-colors font-medium"
                        >
                            Statistics
                        </Link>

                        {/* Status Indicator */}
                        <div className="flex items-center space-x-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/30">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-xs text-green-400 font-medium">Live</span>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    )
}

export default Navbar


