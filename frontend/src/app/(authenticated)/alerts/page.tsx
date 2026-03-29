"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { dashboardApi } from "@/lib/api";

interface AlertItem {
  id: number;
  company_id: number;
  company_name: string;
  event_type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  notified_at: string | null;
}

const SEVERITY_COLORS: Record<string, string> = {
  "高": "bg-red-100 text-red-700 border-red-200",
  "中": "bg-yellow-100 text-yellow-700 border-yellow-200",
  "低": "bg-green-100 text-green-700 border-green-200",
};

const EVENT_LABELS: Record<string, string> = {
  hiring_surge: "採用変動",
  reorg: "組織再編",
  new_service: "新サービス",
  score_change: "スコア変動",
  crawl_failure: "クロール失敗",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filter, setFilter] = useState<{ severity: string; readStatus: string }>({
    severity: "",
    readStatus: "",
  });

  const fetchAlerts = async () => {
    const params: Record<string, unknown> = { limit: 50 };
    if (filter.severity) params.severity = filter.severity;
    if (filter.readStatus === "unread") params.is_read = false;
    if (filter.readStatus === "read") params.is_read = true;

    try {
      const data = await dashboardApi.alerts(params as { severity?: string; is_read?: boolean; limit?: number });
      setAlerts(data as unknown as AlertItem[]);
    } catch {
      // エラー処理
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [filter]);

  const handleMarkRead = async (id: number) => {
    await dashboardApi.markAlertRead(id);
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
  };

  const handleMarkAllRead = async () => {
    await dashboardApi.markAllAlertsRead();
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
  };

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">アラート</h2>
          {unreadCount > 0 && (
            <p className="text-sm text-gray-500 mt-1">{unreadCount}件の未読アラート</p>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-sm text-primary-600 hover:text-primary-800"
          >
            全て既読にする
          </button>
        )}
      </div>

      {/* フィルター */}
      <div className="flex gap-3 mb-6">
        <select
          value={filter.severity}
          onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">全ての重要度</option>
          <option value="高">高</option>
          <option value="中">中</option>
          <option value="低">低</option>
        </select>
        <select
          value={filter.readStatus}
          onChange={(e) => setFilter({ ...filter, readStatus: e.target.value })}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">全て</option>
          <option value="unread">未読のみ</option>
          <option value="read">既読のみ</option>
        </select>
      </div>

      {/* アラート一覧 */}
      {alerts.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <p className="text-gray-500">アラートはありません</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border p-4 transition-colors ${
                alert.is_read ? "border-gray-200" : "border-orange-300 bg-orange-50"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs px-2 py-0.5 rounded border ${SEVERITY_COLORS[alert.severity] || "bg-gray-100"}`}>
                      {alert.severity}
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      {EVENT_LABELS[alert.event_type] || alert.event_type}
                    </span>
                    <Link
                      href={`/companies/${alert.company_id}`}
                      className="text-xs text-primary-600 hover:underline"
                    >
                      {alert.company_name}
                    </Link>
                    {!alert.is_read && (
                      <span className="w-2 h-2 bg-orange-500 rounded-full" />
                    )}
                  </div>
                  <div className="text-sm font-medium text-gray-900">{alert.title}</div>
                  {alert.message && (
                    <div className="text-xs text-gray-500 mt-1 whitespace-pre-line line-clamp-3">{alert.message}</div>
                  )}
                  <div className="text-xs text-gray-400 mt-2">
                    {alert.notified_at ? new Date(alert.notified_at).toLocaleString("ja-JP") : ""}
                  </div>
                </div>
                {!alert.is_read && (
                  <button
                    onClick={() => handleMarkRead(alert.id)}
                    className="text-xs text-gray-500 hover:text-gray-700 ml-4 whitespace-nowrap"
                  >
                    既読にする
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
