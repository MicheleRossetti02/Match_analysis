import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { format } from 'date-fns'

function Statistics() {
    // Fetch model performance
    const { data: modelPerformance, isLoading } = useQuery({
        queryKey: ['modelPerformance'],
        queryFn: () => api.getModelPerformance({ limit: 10 }),
    })

    // Fetch accuracy stats
    const { data: accuracyStats } = useQuery({
        queryKey: ['accuracyStats'],
        queryFn: () => api.getAccuracyStats(),
    })

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
                <h1 className="text-4xl font-bold text-white">Model Statistics</h1>
                <p className="text-gray-400 mt-2">Performance metrics and accuracy analysis</p>
            </div>

            {/* Overall Stats */}
            {accuracyStats?.data && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="card bg-gradient-to-br from-green-600/20 to-green-800/20 border-green-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Overall Accuracy</h3>
                        <p className="text-4xl font-bold text-green-400 mt-2">
                            {accuracyStats.data.accuracy_percent?.toFixed(1) || '0.0'}%
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Total Predictions</h3>
                        <p className="text-4xl font-bold text-blue-400 mt-2">
                            {accuracyStats.data.total_predictions || 0}
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-purple-600/20 to-purple-800/20 border-purple-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Correct Predictions</h3>
                        <p className="text-4xl font-bold text-purple-400 mt-2">
                            {accuracyStats.data.correct_predictions || 0}
                        </p>
                    </div>

                    <div className="card bg-gradient-to-br from-orange-600/20 to-orange-800/20 border-orange-500/30">
                        <h3 className="text-sm text-gray-400 font-medium">Active Model</h3>
                        <p className="text-2xl font-bold text-orange-400 mt-2">
                            {accuracyStats.data.active_model?.type || 'N/A'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            v{accuracyStats.data.active_model?.version || '0.0.0'}
                        </p>
                    </div>
                </div>
            )}

            {/* Model Performance History */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white">Model Performance History</h2>

                {isLoading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
                        <p className="text-gray-400 mt-4">Loading performance data...</p>
                    </div>
                ) : modelPerformance?.data && modelPerformance.data.length > 0 ? (
                    <div className="space-y-3">
                        {modelPerformance.data.map((model) => (
                            <div key={model.id} className="card hover:border-primary-500/50 transition-all">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-4 mb-3">
                                            <h3 className="text-xl font-bold text-white">
                                                {model.model_type}
                                            </h3>
                                            <span className="badge badge-info">v{model.model_version}</span>
                                            {model.is_active && (
                                                <span className="badge badge-success">Active</span>
                                            )}
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                                            <div>
                                                <p className="text-xs text-gray-400">Accuracy</p>
                                                <p className="text-lg font-semibold text-primary-400">
                                                    {(model.accuracy * 100).toFixed(1)}%
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-400">F1 Score</p>
                                                <p className="text-lg font-semibold text-blue-400">
                                                    {model.f1_score ? (model.f1_score * 100).toFixed(1) + '%' : 'N/A'}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-400">Training Samples</p>
                                                <p className="text-lg font-semibold text-purple-400">
                                                    {model.training_samples || 'N/A'}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-400">Trained</p>
                                                <p className="text-sm font-medium text-gray-300">
                                                    {format(new Date(model.trained_at), 'PP')}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="card text-center py-12">
                        <div className="text-6xl mb-4">📊</div>
                        <h3 className="text-xl font-bold text-white mb-2">No Model Data Available</h3>
                        <p className="text-gray-400">
                            Train your first model to see performance statistics here.
                        </p>
                    </div>
                )}
            </div>

            {/* Info Card */}
            <div className="card bg-blue-600/10 border-blue-500/30">
                <div className="flex items-start space-x-4">
                    <div className="text-3xl">ℹ️</div>
                    <div>
                        <h3 className="font-bold text-white mb-2">About Model Performance</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">
                            Our machine learning models are continuously trained on historical match data from the top 5 European leagues.
                            The accuracy shows how often the model correctly predicts match outcomes. Models are retrained bi-weekly
                            to incorporate the latest data and improve predictions.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Statistics
