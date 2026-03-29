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
  title: string;
  summary: string | null;
  impact_score: string | null;
  tags: string[] | null;
  source: string;
  published_at: string | null;
}

interface CompanyDigest {
  company_id: number;
  company_name: string;
  total_count: number;
  summary: string;
  high_impact: NewsItem[];
  mid_impact: NewsItem[];
  other: NewsItem[];
  recruiter_highlights: string[];
}

interface NewsDigest {
  company_digests: CompanyDigest[];
  top_highlights: Array<{ company_name: string; title: string; summary: string | null; tags: string[] | null }>;
  total_articles: number;
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
  "高": "bg-red-100 text-red-700 border-red-200",
  "中": "bg-yellow-100 text-yellow-700 border-yellow-200",
  "低": "bg-green-100 text-green-700 border-green-200",
};

const SEVERITY_BADGE: Record<string, string> = {
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
  const [digest, setDigest] = useState<NewsDigest | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [expandedCompany, setExpandedCompany] = useState<number | null>(null);

  useEffect(() => {
    dashboardApi.stats().then(setStats).catch(() => {});
    dashboardApi.newsDigest().then((data) => setDigest(data as unknown as NewsDigest)).catch(() => {});
    dashboardApi.alerts({ limit: 5 }).then((data) => setAlerts(data as unknown as AlertItem[])).catch(() => {});
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">業界オーバービュー</h2>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="登録企業数" value={stats?.company_count ?? "-"} />
        <StatCard label="ニュース記事" value={stats?.news_count ?? "-"} />
        <StatCard label="未読アラート" value={stats?.unread_alerts ?? "-"} highlight={!!stats && stats.unread_alerts > 0} />
        <StatCard label="アクティブ求人" value={stats?.job_count ?? "-"} />
      </div>

      {/* 重要ニュースハイライト */}
      {digest && digest.top_highlights && digest.top_highlights.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 mb-6">
          <h3 className="text-base font-semibold text-red-800 mb-3">重要ニュース</h3>
          <div className="space-y-3">
            {digest.top_highlights.map((item, i) => (
              <div key={i} className="bg-white border border-red-100 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-medium">重要</span>
                  <span className="text-xs text-gray-500">{item.company_name}</span>
                </div>
                <div className="text-sm font-medium text-gray-900">{item.title}</div>
                {item.summary && (
                  <div className="text-xs text-gray-600 mt-1">{item.summary}</div>
                )}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex gap-1 mt-2">
                    {item.tags.map((tag, j) => (
                      <span key={j} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ニュースダイジェスト（企業別） */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ニュースダイジェスト
              {digest && <span className="text-sm font-normal text-gray-500 ml-2">（{digest.total_articles}件）</span>}
            </h3>

            {!digest || digest.company_digests.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-2">ニュースがありません</p>
                <p className="text-sm text-gray-400">
                  管理画面で企業とクロールソースを登録し、クロールを実行してください。
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {digest.company_digests.map((cd) => (
                  <div key={cd.company_id} className="border border-gray-200 rounded-lg overflow-hidden">
                    {/* 企業ヘッダー */}
                    <button
                      className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
                      onClick={() => setExpandedCompany(expandedCompany === cd.company_id ? null : cd.company_id)}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/companies/${cd.company_id}`}
                            className="font-semibold text-gray-900 hover:text-primary-600"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {cd.company_name}
                          </Link>
                          <span className="text-xs text-gray-400">{cd.total_count}件</span>
                          {cd.high_impact.length > 0 && (
                            <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                              重要{cd.high_impact.length}件
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">{cd.summary}</div>
                      </div>
                      <span className="text-gray-400 ml-2">{expandedCompany === cd.company_id ? "▲" : "▼"}</span>
                    </button>

                    {/* 採用担当向けハイライト */}
                    {cd.recruiter_highlights.length > 0 && (
                      <div className="px-4 pb-2">
                        <div className="bg-primary-50 border border-primary-100 rounded-lg p-3">
                          <div className="text-xs font-medium text-primary-700 mb-1">採用担当者向け注目ポイント</div>
                          {cd.recruiter_highlights.map((hl, i) => (
                            <div key={i} className="text-sm text-primary-800">{hl}</div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 展開時: ニュース詳細 */}
                    {expandedCompany === cd.company_id && (
                      <div className="border-t border-gray-200 p-4 space-y-3 bg-gray-50">
                        {/* 重要ニュース */}
                        {cd.high_impact.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-red-700 mb-2">重要ニュース</div>
                            {cd.high_impact.map((item) => (
                              <NewsCard key={item.id} item={item} />
                            ))}
                          </div>
                        )}
                        {/* 注目ニュース */}
                        {cd.mid_impact.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-yellow-700 mb-2">注目ニュース</div>
                            {cd.mid_impact.map((item) => (
                              <NewsCard key={item.id} item={item} />
                            ))}
                          </div>
                        )}
                        {/* その他 */}
                        {cd.other.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2">その他</div>
                            {cd.other.map((item) => (
                              <NewsCard key={item.id} item={item} />
                            ))}
                          </div>
                        )}
                      </div>
                    )}
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
                      <span className={`text-xs px-2 py-0.5 rounded ${SEVERITY_BADGE[alert.severity] || "bg-gray-100"}`}>
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

/** 統計カード */
function StatCard({ label, value, highlight }: { label: string; value: number | string; highlight?: boolean }) {
  return (
    <div className={`p-5 rounded-xl border ${highlight ? "bg-orange-50 border-orange-200" : "bg-white border-gray-200"}`}>
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`text-3xl font-bold mt-2 ${highlight ? "text-orange-600" : "text-gray-900"}`}>{value}</div>
    </div>
  );
}

/** ニュースカード */
function NewsCard({ item }: { item: NewsItem }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 mb-2">
      <div className="flex items-center gap-2 mb-1">
        {item.impact_score && (
          <span className={`text-xs px-1.5 py-0.5 rounded border ${IMPACT_COLORS[item.impact_score] || ""}`}>
            {item.impact_score}
          </span>
        )}
        <span className="text-xs text-gray-400">{item.source}</span>
        {item.published_at && (
          <span className="text-xs text-gray-400">{new Date(item.published_at).toLocaleDateString("ja-JP")}</span>
        )}
      </div>
      <div className="text-sm font-medium text-gray-900">{item.title}</div>
      {item.summary && (
        <div className="text-xs text-gray-600 mt-1 leading-relaxed">{item.summary}</div>
      )}
      {item.tags && item.tags.length > 0 && (
        <div className="flex gap-1 mt-2">
          {item.tags.map((tag, i) => (
            <span key={i} className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}
