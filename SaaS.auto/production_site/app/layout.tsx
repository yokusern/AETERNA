import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'TimeTracker Pro - エンジニア向け時間管理SaaS',
  description: 'AIが分析する最強の時間管理ツール。プロジェクトごとの時間追跡、収益性分析、生産性向上を自動化。',
  keywords: '時間管理,プロジェクト管理,エンジニア,SaaS,生産性向上,時間追跡',
  openGraph: {
    title: 'TimeTracker Pro',
    description: 'エンジニアのためのAI時間管理SaaS',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </body>
    </html>
  )
}
