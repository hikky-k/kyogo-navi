"use client";

import { useEffect, useState } from "react";
import { companiesApi, dashboardApi } from "@/lib/api";
import { Company } from "@/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface CompanyData {
  company: { id: number; name: string; category: string; description: string | null };
  strength_weakness: {
    strengths?: Array<{ category: string; description: string }>;
    weaknesses?: Array<{ category: string; description: string }>;
    summary?: string;
    attraction_points?: Array<{ theme: string; what_to_say: string }>;
  } | null;
  review: { overall_score: number | null; categories_json: Record<string, number> | null; review_count: number };
  job_count: number;
  news_count: number;
}

interface PairwiseComparison {
  company_1: string;
  company_2: string;
  advantages_1: Array<{ area: string; reason: string }>;
  advantages_2: Array<{ area: string; reason: string }>;
}

interface DiffAnalysis {
  strength_matrix: Array<{ category: string; type: string; [key: string]: string | boolean }>;
  weakness_matrix: Array<{ category: string; type: string; [key: string]: string | boolean }>;
  unique_strengths: Record<string, string[]>;
  unique_weaknesses: Record<string, string[]>;
  pairwise: PairwiseComparison[];
  interview_guide: Array<{ company: string; points: string[] }>;
}

interface CompareResponse {
  companies: CompanyData[];
  diff_analysis: DiffAnalysis;
}

const BAR_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function ComparePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    companiesApi.list({ is_active: true }).then(setCompanies).catch(() => {});
  }, []);

  const handleToggle = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2) return;
    setLoading(true);
    try {
      const data = await dashboardApi.compare(selectedIds);
      setCompareData(data as unknown as CompareResponse);
    } catch {
      // エラー処理
    } finally {
      setLoading(false);
    }
  };

  const cd = compareData?.companies || [];
  const diff = compareData?.diff_analysis;
  const names = cd.map((d) => d.company.name);

  // スコア比較チャート用データ
  const scoreChartData = cd.map((d) => ({
    name: d.company.name,
    "口コミスコア": d.review.overall_score || 0,
    "求人数": d.job_count,
    "ニュース数": d.news_count,
  }));

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">企業比較</h2>

      {/* 企業選択 */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="text-sm font-medium text-gray-700 mb-3">比較する企業を選択（2社以上）</div>
        <div className="flex flex-wrap gap-2 mb-3">
          {companies.map((c) => (
            <button
              key={c.id}
              onClick={() => handleToggle(c.id)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                selectedIds.includes(c.id)
                  ? "bg-primary-600 text-white border-primary-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-primary-400"
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>
        <button
          onClick={handleCompare}
          disabled={selectedIds.length < 2 || loading}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? "比較中..." : "比較する"}
        </button>
      </div>

      {compareData && cd.length > 0 && diff && (
        <>
          {/* === 1対1 差別化ポイント（メインセクション） === */}
          {diff.pairwise && diff.pairwise.length > 0 && (
            <div className="bg-white rounded-xl border-2 border-primary-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-primary-800 mb-4">差別化ポイント（1対1比較）</h3>
              <div className="space-y-6">
                {diff.pairwise.map((pair, i) => (
                  <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-2 text-sm font-semibold text-gray-700 text-center">
                      {pair.company_1} vs {pair.company_2}
                    </div>
                    <div className="grid grid-cols-2 divide-x divide-gray-200">
                      {/* 左: company_1の優位点 */}
                      <div className="p-4">
                        <div className="text-xs font-semibold text-blue-700 mb-2">{pair.company_1} の優位点</div>
                        {pair.advantages_1.length > 0 ? (
                          <div className="space-y-1.5">
                            {pair.advantages_1.map((a, j) => (
                              <div key={j} className="bg-blue-50 p-2 rounded text-xs">
                                <div className="font-medium text-blue-800">{a.area}</div>
                                <div className="text-blue-600 mt-0.5">{a.reason}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-gray-400">明確な優位点なし</p>
                        )}
                      </div>
                      {/* 右: company_2の優位�� */}
                      <div className="p-4">
                        <div className="text-xs font-semibold text-emerald-700 mb-2">{pair.company_2} の優位点</div>
                        {pair.advantages_2.length > 0 ? (
                          <div className="space-y-1.5">
                            {pair.advantages_2.map((a, j) => (
                              <div key={j} className="bg-emerald-50 p-2 rounded text-xs">
                                <div className="font-medium text-emerald-800">{a.area}</div>
                                <div className="text-emerald-600 mt-0.5">{a.reason}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-gray-400">明確な優位点なし</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* === 強み比較マ���リクス === */}
          {diff.strength_matrix && diff.strength_matrix.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">強み比較マトリクス</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 text-gray-600 font-medium">項目</th>
                      {names.map((name, i) => (
                        <th key={name} className="text-center py-2 px-3 font-medium" style={{ color: BAR_COLORS[i % BAR_COLORS.length] }}>
                          {name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {diff.strength_matrix.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-gray-700">{row.category}</td>
                        {names.map((name) => (
                          <td key={name} className="text-center py-2 px-3">
                            {row[name] ? (
                              <span className="inline-block w-6 h-6 bg-green-100 text-green-700 rounded-full leading-6 text-xs font-bold">&#10003;</span>
                            ) : (
                              <span className="inline-block w-6 h-6 bg-gray-100 text-gray-400 rounded-full leading-6 text-xs">-</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* === 弱み比較マトリクス === */}
          {diff.weakness_matrix && diff.weakness_matrix.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">弱み・懸念事項比較マトリクス</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 text-gray-600 font-medium">項目</th>
                      {names.map((name, i) => (
                        <th key={name} className="text-center py-2 px-3 font-medium" style={{ color: BAR_COLORS[i % BAR_COLORS.length] }}>
                          {name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {diff.weakness_matrix.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-gray-700">{row.category}</td>
                        {names.map((name) => (
                          <td key={name} className="text-center py-2 px-3">
                            {row[name] ? (
                              <span className="inline-block w-6 h-6 bg-red-100 text-red-600 rounded-full leading-6 text-xs font-bold">!</span>
                            ) : (
                              <span className="inline-block w-6 h-6 bg-gray-100 text-gray-400 rounded-full leading-6 text-xs">-</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* === ユニークな強み/弱み === */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">各社固有の特徴（他社にないもの）</h3>
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cd.length}, 1fr)` }}>
              {cd.map((d, i) => {
                const uStr = diff.unique_strengths?.[d.company.name] || [];
                const uWeak = diff.unique_weaknesses?.[d.company.name] || [];
                return (
                  <div key={d.company.id} className="border rounded-lg p-4" style={{ borderColor: BAR_COLORS[i % BAR_COLORS.length] }}>
                    <div className="font-semibold text-gray-900 mb-3">{d.company.name}</div>
                    {uStr.length > 0 && (
                      <div className="mb-3">
                        <div className="text-xs font-medium text-green-700 mb-1">他社にない強み</div>
                        {uStr.map((s, j) => (
                          <span key={j} className="inline-block bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded mr-1 mb-1">{s}</span>
                        ))}
                      </div>
                    )}
                    {uWeak.length > 0 && (
                      <div className="mb-3">
                        <div className="text-xs font-medium text-red-700 mb-1">他社にない��み</div>
                        {uWeak.map((w, j) => (
                          <span key={j} className="inline-block bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded mr-1 mb-1">{w}</span>
                        ))}
                      </div>
                    )}
                    {uStr.length === 0 && uWeak.length === 0 && (
                      <p className="text-xs text-gray-400">他社と類似した特性</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* === スコア・数値比較チャート === */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">数値比較</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="口コミスコア" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="求人数" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="ニュース数" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* === 面接での使い方ガイド === */}
          {diff.interview_guide && diff.interview_guide.length > 0 && (
            <div className="bg-white rounded-xl border-2 border-amber-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-amber-800 mb-4">面接での活用ガイド</h3>
              <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cd.length}, 1fr)` }}>
                {diff.interview_guide.map((guide, i) => (
                  <div key={i} className="bg-amber-50 p-4 rounded-lg">
                    <div className="font-semibold text-amber-900 mb-2">{guide.company}</div>
                    <ul className="space-y-1.5">
                      {guide.points.map((point, j) => (
                        <li key={j} className="text-sm text-amber-800 flex items-start gap-2">
                          <span className="text-amber-500 mt-0.5">-</span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
