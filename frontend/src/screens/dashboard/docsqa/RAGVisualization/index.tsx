import React, { useState, useEffect } from 'react'
import Button from '@/components/base/atoms/Button'
import Input from '@/components/base/atoms/Input'
import Badge from '@/components/base/atoms/Badge'
import IconProvider from '@/components/assets/IconProvider'
import { baseQAFoundryPath } from '@/stores/qafoundry'

interface RAGStep {
    step_id: string
    step_type: string
    step_name: string
    status: 'pending' | 'in_progress' | 'completed' | 'failed'
    start_time?: string
    end_time?: string
    duration_ms?: number
    input_data?: any
    output_data?: any
    metadata?: any
    error_message?: string
}

interface RetrievedDocument {
    document: {
        page_content: string
        metadata: any
    }
    similarity_score?: number
    rerank_score?: number
    retrieval_method?: string
    chunk_index?: number
}

interface RAGVisualizationData {
    query_id: string
    original_query: string
    processed_query?: string
    collection_name: string
    model_configuration: any
    retriever_config: any
    steps: RAGStep[]
    retrieved_documents: RetrievedDocument[]
    final_answer?: string
    total_duration_ms?: number
    metrics?: any
}

interface RAGVisualizationResponse {
    answer: string
    visualization_data: RAGVisualizationData
    docs: any[]
}

const RAGVisualization: React.FC = () => {
    const [query, setQuery] = useState('What are credit cards?')
    const [collectionName, setCollectionName] = useState('test-rag-collection')
    const [isLoading, setIsLoading] = useState(false)
    const [visualizationData, setVisualizationData] = useState<RAGVisualizationData | null>(null)
    const [answer, setAnswer] = useState('')
    const [activeTab, setActiveTab] = useState('query')

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <IconProvider icon="fa-check-circle" className="text-green-500" size={0.75} />
            case 'failed':
                return <IconProvider icon="fa-exclamation-circle" className="text-red-500" size={0.75} />
            case 'in_progress':
                return <IconProvider icon="fa-clock" className="text-blue-500 animate-spin" size={0.75} />
            default:
                return <IconProvider icon="fa-clock" className="text-gray-400" size={0.75} />
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800'
            case 'failed':
                return 'bg-red-100 text-red-800'
            case 'in_progress':
                return 'bg-blue-100 text-blue-800'
            default:
                return 'bg-gray-100 text-gray-800'
        }
    }

    const handleSubmit = async () => {
        if (!query.trim() || !collectionName.trim()) return

        setIsLoading(true)
        setVisualizationData(null)
        setAnswer('')

        try {
            const payload = {
                collection_name: collectionName,
                query: query,
                model_configuration: {
                    name: "local-ollama/qwen2:1.5b",
                    type: "chat"
                },
                prompt_template: "Based on the context below, answer the question.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:",
                retriever_name: "vectorstore",
                retriever_config: {
                    search_type: "similarity",
                    search_kwargs: {
                        k: 3
                    },
                    filter: {}
                },
                stream: false
            }

            const response = await fetch(`${baseQAFoundryPath}/retrievers/rag-visualization/answer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            })

            if (!response.ok) {
                throw new Error('Failed to get RAG visualization')
            }

            const data: RAGVisualizationResponse = await response.json()
            setVisualizationData(data.visualization_data)
            setAnswer(data.answer)
            setActiveTab('pipeline')
        } catch (error) {
            console.error('Error:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const formatDuration = (ms?: number) => {
        if (!ms) return 'N/A'
        if (ms < 1000) return `${ms}ms`
        return `${(ms / 1000).toFixed(2)}s`
    }

    return (
        <div className="max-w-7xl mx-auto overflow-auto p-6 space-y-6">
            <div className="border rounded-lg border-gray-200 bg-white p-6">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <IconProvider icon="fa-eye" size={1} />
                        RAG Pipeline Visualization
                    </h2>
                </div>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">Collection Name</label>
                        <Input
                            value={collectionName}
                            onChange={(e) => setCollectionName(e.target.value)}
                            placeholder="Enter collection name"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2">Query</label>
                        <textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Enter your question"
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <Button
                        onClick={handleSubmit}
                        disabled={isLoading || !query.trim() || !collectionName.trim()}
                        className="w-full"
                        text={isLoading ? "Processing..." : "Run RAG Pipeline"}
                        icon={isLoading ? "fa-clock" : "fa-play"}
                        loading={isLoading}
                    />
                </div>
            </div>

            {visualizationData && (
                <div className="h-96 overflow-y-auto border rounded-lg border-gray-200 bg-white">
                    <div className="border-b border-gray-200 mb-6 sticky top-0 bg-white z-10">
                        <nav className="flex space-x-8 p-4 pb-0">
                            {[
                                { id: 'pipeline', label: 'Pipeline Steps' },
                                { id: 'documents', label: 'Retrieved Documents' },
                                { id: 'answer', label: 'Generated Answer' },
                                { id: 'metrics', label: 'Performance Metrics' }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>

                    {activeTab === 'pipeline' && (
                        <div className="p-6">
                            <h3 className="text-lg font-semibold mb-4">Pipeline Execution Steps</h3>
                            <div className="space-y-4">
                                {visualizationData.steps.map((step, index) => (
                                    <div key={step.step_id} className="border rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                {getStatusIcon(step.status)}
                                                <span className="font-medium">{step.step_name}</span>
                                                <Badge
                                                    text={step.status}
                                                    className={getStatusColor(step.status)}
                                                />
                                            </div>
                                            <span className="text-sm text-gray-500">
                                                {formatDuration(step.duration_ms)}
                                            </span>
                                        </div>

                                        {step.error_message && (
                                            <div className="text-red-600 text-sm mb-2">
                                                Error: {step.error_message}
                                            </div>
                                        )}

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                            {step.input_data && Object.keys(step.input_data).length > 0 && (
                                                <div>
                                                    <span className="font-medium text-gray-700">Input:</span>
                                                    <pre className="bg-gray-50 p-2 rounded mt-1 text-xs overflow-x-auto">
                                                        {JSON.stringify(step.input_data, null, 2)}
                                                    </pre>
                                                </div>
                                            )}

                                            {step.output_data && Object.keys(step.output_data).length > 0 && (
                                                <div>
                                                    <span className="font-medium text-gray-700">Output:</span>
                                                    <pre className="bg-gray-50 p-2 rounded mt-1 text-xs overflow-x-auto">
                                                        {JSON.stringify(step.output_data, null, 2)}
                                                    </pre>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'documents' && (
                        <div className="p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <IconProvider icon="fa-file-text" size={1} />
                                Retrieved Documents ({visualizationData.retrieved_documents.length})
                            </h3>
                            <div className="space-y-4">
                                {visualizationData.retrieved_documents.map((doc, index) => (
                                    <div key={index} className="border rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium">Document {index + 1}</span>
                                            <div className="flex gap-2">
                                                {doc.similarity_score && (
                                                    <Badge
                                                        text={`Similarity: ${doc.similarity_score.toFixed(3)}`}
                                                        className="bg-blue-100 text-blue-800"
                                                    />
                                                )}
                                                {doc.rerank_score && (
                                                    <Badge
                                                        text={`Rerank: ${doc.rerank_score.toFixed(3)}`}
                                                        className="bg-purple-100 text-purple-800"
                                                    />
                                                )}
                                            </div>
                                        </div>

                                        <div className="text-sm text-gray-600 mb-2">
                                            Method: {doc.retrieval_method || 'N/A'} |
                                            Chunk: {doc.chunk_index !== undefined ? doc.chunk_index : 'N/A'}
                                        </div>

                                        <div className="bg-gray-50 p-3 rounded text-sm">
                                            <div className="font-medium mb-1">Content:</div>
                                            <div className="whitespace-pre-wrap">
                                                {doc.document.page_content.substring(0, 500)}
                                                {doc.document.page_content.length > 500 && '...'}
                                            </div>
                                        </div>

                                        {doc.document.metadata && Object.keys(doc.document.metadata).length > 0 && (
                                            <div className="mt-2">
                                                <div className="font-medium text-sm mb-1">Metadata:</div>
                                                <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                                                    {JSON.stringify(doc.document.metadata, null, 2)}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'answer' && (
                        <div className="p-6">
                            <h3 className="text-lg font-semibold mb-4">Generated Answer</h3>
                            <div className="space-y-4">
                                <div className="bg-blue-50 p-4 rounded-lg">
                                    <div className="font-medium text-blue-900 mb-2">Query:</div>
                                    <div className="text-blue-800">{visualizationData.original_query}</div>
                                </div>

                                <div className="bg-green-50 p-4 rounded-lg">
                                    <div className="font-medium text-green-900 mb-2">Answer:</div>
                                    <div className="text-green-800 whitespace-pre-wrap">{answer}</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'metrics' && (
                        <div className="p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <IconProvider icon="fa-bolt" size={1} />
                                Performance Metrics
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="bg-blue-50 p-4 rounded-lg">
                                    <div className="text-2xl font-bold text-blue-600">
                                        {formatDuration(visualizationData.total_duration_ms)}
                                    </div>
                                    <div className="text-sm text-blue-800">Total Duration</div>
                                </div>

                                <div className="bg-green-50 p-4 rounded-lg">
                                    <div className="text-2xl font-bold text-green-600">
                                        {visualizationData.steps.length}
                                    </div>
                                    <div className="text-sm text-green-800">Pipeline Steps</div>
                                </div>

                                <div className="bg-purple-50 p-4 rounded-lg">
                                    <div className="text-2xl font-bold text-purple-600">
                                        {visualizationData.retrieved_documents.length}
                                    </div>
                                    <div className="text-sm text-purple-800">Retrieved Docs</div>
                                </div>

                                <div className="bg-orange-50 p-4 rounded-lg">
                                    <div className="text-2xl font-bold text-orange-600">
                                        {visualizationData.steps.filter(s => s.status === 'completed').length}
                                    </div>
                                    <div className="text-sm text-orange-800">Successful Steps</div>
                                </div>
                            </div>

                            {visualizationData.metrics && (
                                <div className="mt-6">
                                    <h3 className="font-medium mb-3">Detailed Metrics</h3>
                                    <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto">
                                        {JSON.stringify(visualizationData.metrics, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default RAGVisualization