'use client'

import { useState, useEffect } from 'react'
import { Clock, Play, Pause, Square, TrendingUp, DollarSign, Activity, Calendar, BarChart3 } from 'lucide-react'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { ProgressBar } from './components/ProgressBar'

interface TimeEntry {
  id: string
  project: string
  description: string
  startTime: Date
  endTime?: Date
  duration?: number
  hourlyRate?: number
  earnings?: number
}

interface Project {
  id: string
  name: string
  color: string
  hourlyRate: number
  totalTime: number
  earnings: number
}

export default function TimeTrackerPro() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isTracking, setIsTracking] = useState(false)
  const [currentProject, setCurrentProject] = useState('')
  const [currentDescription, setCurrentDescription] = useState('')
  const [entries, setEntries] = useState<TimeEntry[]>([])
  const [projects, setProjects] = useState<Project[]>([
    { id: '1', name: 'AETERNA開発', color: 'bg-blue-500', hourlyRate: 5000, totalTime: 0, earnings: 0 },
    { id: '2', name: 'クライアント作業', color: 'bg-green-500', hourlyRate: 8000, totalTime: 0, earnings: 0 },
    { id: '3', name: '学習・研究', color: 'bg-purple-500', hourlyRate: 0, totalTime: 0, earnings: 0 },
  ])

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const startTracking = () => {
    if (!currentProject || !currentDescription) return
    
    const newEntry: TimeEntry = {
      id: Date.now().toString(),
      project: currentProject,
      description: currentDescription,
      startTime: new Date(),
    }
    
    setEntries([newEntry, ...entries])
    setIsTracking(true)
  }

  const stopTracking = () => {
    if (!isTracking) return
    
    const endTime = new Date()
    const updatedEntries = entries.map(entry => {
      if (entry.id === entries[0].id) {
        const duration = (endTime.getTime() - entry.startTime.getTime()) / 1000 / 60 / 60 // 時間
        const project = projects.find(p => p.name === entry.project)
        const earnings = project ? duration * project.hourlyRate : 0
        
        return {
          ...entry,
          endTime,
          duration,
          earnings
        }
      }
      return entry
    })
    
    setEntries(updatedEntries)
    setIsTracking(false)
    setCurrentProject('')
    setCurrentDescription('')
    
    // プロジェクト時間を更新
    const updatedProjects = projects.map(project => {
      if (project.name === currentProject) {
        const entry = updatedEntries[0]
        return {
          ...project,
          totalTime: project.totalTime + (entry.duration || 0),
          earnings: project.earnings + (entry.earnings || 0)
        }
      }
      return project
    })
    setProjects(updatedProjects)
  }

  const totalEarnings = projects.reduce((sum, project) => sum + project.earnings, 0)
  const totalHours = projects.reduce((sum, project) => sum + project.totalTime, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <Clock className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">TimeTracker Pro</h1>
            </div>
            <div className="text-sm text-gray-500">
              {format(currentTime, 'yyyy年MM月dd日 HH:mm:ss', { locale: ja })}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="dashboard-grid mb-8">
          <div className="stats-card stats-card-primary">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">総稼働時間</p>
                <p className="text-2xl font-bold text-gray-900">{totalHours.toFixed(1)}時間</p>
              </div>
              <Clock className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          
          <div className="stats-card stats-card-success">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">総収益</p>
                <p className="text-2xl font-bold text-gray-900">¥{totalEarnings.toLocaleString()}</p>
              </div>
              <DollarSign className="w-8 h-8 text-success-600" />
            </div>
          </div>
          
          <div className="stats-card stats-card-warning">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">平均時給</p>
                <p className="text-2xl font-bold text-gray-900">
                  ¥{totalHours > 0 ? Math.round(totalEarnings / totalHours).toLocaleString() : 0}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-warning-600" />
            </div>
          </div>
        </div>

        {/* Time Tracking Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Tracking Controls */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">時間記録</h2>
            
            <div className="space-y-4">
              <div>
                <label className="label">プロジェクト</label>
                <select
                  value={currentProject}
                  onChange={(e) => setCurrentProject(e.target.value)}
                  className="input"
                  disabled={isTracking}
                  aria-label="プロジェクトを選択"
                  title="プロジェクトを選択"
                >
                  <option value="">プロジェクトを選択</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.name}>
                      {project.name} (¥{project.hourlyRate.toLocaleString()}/h)
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="label">作業内容</label>
                <input
                  type="text"
                  value={currentDescription}
                  onChange={(e) => setCurrentDescription(e.target.value)}
                  className="input"
                  placeholder="例：AETERNA憲法の実装"
                  disabled={isTracking}
                />
              </div>
              
              <div className="flex space-x-3">
                {!isTracking ? (
                  <button
                    onClick={startTracking}
                    disabled={!currentProject || !currentDescription}
                    className="btn btn-primary flex-1"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    開始
                  </button>
                ) : (
                  <button
                    onClick={stopTracking}
                    className="btn btn-danger flex-1"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    停止
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Current Status */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">現在の状況</h2>
            
            {isTracking && entries.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-gray-700">記録中</span>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">
                    プロジェクト: <span className="font-medium">{entries[0].project}</span>
                  </p>
                  <p className="text-sm text-gray-600 mb-2">
                    作業内容: <span className="font-medium">{entries[0].description}</span>
                  </p>
                  <p className="text-lg font-semibold text-gray-900">
                    経過時間: {format(currentTime, 'HH:mm:ss', { locale: ja })}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">現在記録中の作業はありません</p>
              </div>
            )}
          </div>
        </div>

        {/* Project Summary */}
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">プロジェクト概要</h2>
          
          <div className="overflow-x-auto">
            <table className="time-table">
              <thead>
                <tr>
                  <th>プロジェクト</th>
                  <th>総時間</th>
                  <th>時給</th>
                  <th>収益</th>
                  <th>進捗</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(project => (
                  <tr key={project.id}>
                    <td className="font-medium">{project.name}</td>
                    <td>{project.totalTime.toFixed(1)}時間</td>
                    <td>¥{project.hourlyRate.toLocaleString()}</td>
                    <td className="font-semibold">¥{project.earnings.toLocaleString()}</td>
                    <td>
                      <ProgressBar 
                        percentage={(project.totalTime / 100) * 100}
                        className="w-full bg-gray-200 rounded-full h-2"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Entries */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">最近の記録</h2>
          
          <div className="space-y-3">
            {entries.slice(0, 10).map(entry => (
              <div key={entry.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{entry.description}</p>
                  <p className="text-sm text-gray-600">{entry.project}</p>
                </div>
                <div className="text-right">
                  {entry.endTime ? (
                    <>
                      <p className="font-semibold text-gray-900">
                        {entry.duration?.toFixed(1)}時間
                      </p>
                      {entry.earnings && entry.earnings > 0 && (
                        <p className="text-sm text-success-600 font-medium">
                          ¥{entry.earnings.toLocaleString()}
                        </p>
                      )}
                    </>
                  ) : (
                    <span className="status-badge status-active">記録中</span>
                  )}
                </div>
              </div>
            ))}
            
            {entries.length === 0 && (
              <div className="text-center py-8">
                <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">記録がありません</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
