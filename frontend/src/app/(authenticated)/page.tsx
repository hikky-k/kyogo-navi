"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { dashboardApi } from "@/lib/api";

interface Stats {
  company_count: number;
  news_count: number;
  unread_alerts: number;
  job_count: number;
}

interface NewsItem {
  id: number;
  company_id: number;
  company_name: string;
  title: string;
  summary: string | null;
  impact_score: string | null;
  source: string;
  tags: string[] | null;
  published_at: string | null;
  created_at: string | null;
}

interface AlertItem {
  id: number;
  company_id: number;
  company_name: string;
  event_type: string;
  severity: string;
  title: string;
  is_read: boolean;
  notified_at: string | null;
}

const IMPACT_COLORS: Record<string, string> = {
  "高": "bg-red-100 text-red-700",
  "中": "bg-yellow-100 text-yellow-700",
  "低": "bg-green-100 text-green-700",
};

const EVENT_LABELS: Record<string, string> = {
  hiring_surge: "採用変動",
  reorg: "組織再編",
  new_service: "新サービス",
  score_change: "スコア変動",
  crawl_failure: "クロール失敗",
};

export default function HomePage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    dashboardApi.stats().then(setStats).catch(() => {});
    dashboardApi.news({ limit: 10 }).then((data) => setNews(data as unknown as NewsItem[])).catch(() => {});
    dashboardApi.alerts({ limit: 5 }).then((data) => setAlerts(data as unknown as AlertItem[])).catch(() => {});
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        業界オーバービュー
      </h2>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="登録企業数" value={stats?.company_count ?? "-"} />
        <StatCard label="ニュース記事" value={stats?.news_count ?? "-"} />
        <StatCard label="未読アラート" value={stats?.unread_alerts ?? "-"} highlight={!!stats && stats.unread_alerts > 0} />
        <StatCard label="アクティブ求人" value={stats?.job_count ?? "-"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 最新ニュース */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">最新ニュース</h3>
            {news.length === 0 ? (
              <p className="text-sm text-gray-500">
                ニュースがありません。管理画面で企業とソースを登録し、クロールを実行してください。
              </p>
            ) : (
              <div className="space-y-3">
                {news.map((item) => (
                  <div key={item.id} className="border-b border-gray-100 pb-3 last:border-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Link
                            href={`/companies/${item.company_id}`}
                            className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded hover:bg-primary-100"
                          >
                            {item.company_name}
                          </Link>
                          {item.impact_score && (
                            <span className={`text-xs px-2 py-0.5 rounded ${IMPACT_COLORS[item.impact_score] || "bg-gray-100 text-gray-600"}`}>
                              {item.impact_score}
                            </span>
                          )}
                          {item.tags?.map((tag) => (
                            <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                        <div className="text-sm font-medium text-gray-900">{item.title}</div>
                        {item.summary && (
                          <div className="text-xs text-gray-500 mt-1 line-clamp-2">{item.summary}</div>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 whitespace-nowrap">
                        {item.published_at
                          ? new Date(item.published_at).toLocaleDateString("ja-JP")
                          : item.created_at
                          ? new Date(item.created_at).toLocaleDateString("ja-JP")
                          : ""}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* アラート */}
        <div>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">アラート</h3>
              <Link href="/alerts" className="text-xs text-primary-600 hover:text-primary-800">
                全て見る
              </Link>
            </div>
            {alerts.length === 0 ? (
              <p className="text-sm text-gray-500">アラートはありません</p>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className={`p-3 rounded-lg border ${alert.is_read ? "bg-gray-50 border-gray-200" : "bg-orange-50 border-orange-200"}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded ${IMPACT_COLORS[alert.severity] || "bg-gray-100"}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs text-gray-500">
                        {EVENT_LABELS[alert.event_type] || alert.event_type}
                      </span>
                    </div>
                    <div className="text-sm text-gray-900">{alert.title}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {alert.notified_at ? new Date(alert.notified_at).toLocaleDateString("ja-JP") : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: number | string; highlight?: boolean }) {
  return (
    <div className={`p-5 rounded-xl border ${highlight ? "bg-orange-50 border-orange-200" : "bg-white border-gray-200"}`}>
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`text-3xl font-bold mt-2 ${highlight ? "text-orange-600" : "text-gray-900"}`}>{value}</div>
    </div>
  );
}
