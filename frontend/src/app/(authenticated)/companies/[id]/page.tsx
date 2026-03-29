"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { companiesApi, dashboardApi, analysisApi } from "@/lib/api";
import { Company } from "@/types";
import ReviewChart from "@/components/ReviewChart";

interface AnalysisData {
  strength_weakness?: {
    content_json: {
      strengths?: Array<{ category: string; description: string; evidence: string }>;
      weaknesses?: Array<{ category: string; description: string; evidence: string }>;
      summary?: string;
      attraction_points?: Array<{ theme: string; what_to_say: string; keywords_found?: string[] }>;
      differentiation_points?: Array<{ point: string; detail: string }>;
      counter_arguments?: Array<{ weakness: string; how_to_address: string }>;
      interview_tips?: string[];
    };
    analyzed_at: string;
  };
}

interface NewsItem {
  id: number;
  title: string;
  summary: string | null;
  impact_score: string | null;
  source: string;
  published_at: string | null;
}

interface JobItem {
  id: number;
  title: string;
  department: string | null;
  salary_range: string | null;
  source: string;
  is_active: boolean;
}

interface ReviewItem {
  overall_score: number;
  source: string;
  categories_json: Record<string, number> | null;
  review_count: number;
  scraped_at: string;
}

const IMPACT_COLORS: Record<string, string> = {
  "高": "bg-red-100 text-red-700",
  "中": "bg-yellow-100 text-yellow-700",
  "低": "bg-green-100 text-green-700",
};

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = Number(params.id);

  const [company, setCompany] = useState<Company | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData>({});
  const [news, setNews] = useState<NewsItem[]>([]);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeMessage, setAnalyzeMessage] = useState("");

  useEffect(() => {
    if (!companyId) return;
    companiesApi.get(companyId).then(setCompany).catch(() => {});
    analysisApi.latest(companyId).then((data) => setAnalysis(data as AnalysisData)).catch(() => {});
    dashboardApi.news({ company_id: companyId, limit: 15 }).then((data) => setNews(data as unknown as NewsItem[])).catch(() => {});
    dashboardApi.companyJobs(companyId).then((data) => setJobs(data as unknown as JobItem[])).catch(() => {});
    dashboardApi.companyReviews(companyId).then((data) => setReviews(data as unknown as ReviewItem[])).catch(() => {});
  }, [companyId]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setAnalyzeMessage("");
    try {
      await analysisApi.run(companyId);
      setAnalyzeMessage("分析完了");
      // 結果を再取得
      const data = await analysisApi.latest(companyId);
      setAnalysis(data as AnalysisData);
    } catch {
      setAnalyzeMessage("分析に失敗しました");
    } finally {
      setAnalyzing(false);
    }
  };

  if (!company) {
    return <div className="text-gray-500">読み込み中...</div>;
  }

  const sw = analysis?.strength_weakness?.content_json;

  return (
    <div>
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{company.name}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{company.category}</span>
            {company.website_url && (
              <a href={company.website_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary-600 hover:underline">
                公式サイト
              </a>
            )}
          </div>
          {company.description && (
            <p className="text-sm text-gray-500 mt-2">{company.description}</p>
          )}
        </div>
        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50"
        >
          {analyzing ? "分析中..." : "AI分析実行"}
        </button>
      </div>

      {analyzeMessage && (
        <div className="bg-blue-50 text-blue-700 text-sm p-3 rounded-lg mb-4">{analyzeMessage}</div>
      )}

      {/* 面接での魅力づけポイント（メインセクション） */}
      {sw && (sw.attraction_points?.length > 0 || sw.differentiation_points?.length > 0 || sw.interview_tips?.length > 0) && (
        <div className="bg-white rounded-xl border-2 border-primary-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-primary-800 mb-4">面接での魅力づけガイド</h3>

          {/* 魅力づけポイント */}
          {sw.attraction_points && sw.attraction_points.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-primary-700 mb-3">候補者に伝えるべきポイント</h4>
              <div className="space-y-2">
                {sw.attraction_points.map((ap: { theme: string; what_to_say: string; keywords_found?: string[] }, i: number) => (
                  <div key={i} className="bg-primary-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-primary-900">{ap.theme}</div>
                    <div className="text-sm text-primary-700 mt-1">{ap.what_to_say}</div>
                    {ap.keywords_found && ap.keywords_found.length > 0 && (
                      <div className="flex gap-1 mt-2">
                        {ap.keywords_found.map((kw: string, j: number) => (
                          <span key={j} className="text-xs bg-primary-100 text-primary-600 px-1.5 py-0.5 rounded">{kw}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 差別化ポイント */}
          {sw.differentiation_points && sw.differentiation_points.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-emerald-700 mb-3">他社との差別化ポイント</h4>
              <div className="space-y-2">
                {sw.differentiation_points.map((dp: { point: string; detail: string }, i: number) => (
                  <div key={i} className="bg-emerald-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-emerald-900">{dp.point}</div>
                    <div className="text-sm text-emerald-700 mt-1">{dp.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 弱みへの切り返しトーク */}
          {sw.counter_arguments && sw.counter_arguments.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-amber-700 mb-3">候補者の懸念への切り返し</h4>
              <div className="space-y-2">
                {sw.counter_arguments.map((ca: { weakness: string; how_to_address: string }, i: number) => (
                  <div key={i} className="bg-amber-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-amber-900">懸念: {ca.weakness}</div>
                    <div className="text-sm text-amber-700 mt-1">{ca.how_to_address}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 面接Tips */}
          {sw.interview_tips && sw.interview_tips.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">面接Tips</h4>
              <ul className="space-y-1.5">
                {sw.interview_tips.map((tip: string, i: number) => (
                  <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-primary-500 mt-0.5">-</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 強み/弱み */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">強み / 弱み分析</h3>
          {sw ? (
            <div className="space-y-4">
              {sw.summary && (
                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{sw.summary}</p>
              )}
              {sw.strengths && sw.strengths.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-green-700 mb-2">強み</h4>
                  <div className="space-y-2">
                    {sw.strengths.map((s, i) => (
                      <div key={i} className="bg-green-50 p-3 rounded-lg">
                        <div className="text-sm font-medium text-green-800">{s.category}</div>
                        <div className="text-sm text-green-700 mt-1">{s.description}</div>
                        <div className="text-xs text-green-600 mt-1">{s.evidence}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {sw.weaknesses && sw.weaknesses.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-red-700 mb-2">弱み</h4>
                  <div className="space-y-2">
                    {sw.weaknesses.map((w, i) => (
                      <div key={i} className="bg-red-50 p-3 rounded-lg">
                        <div className="text-sm font-medium text-red-800">{w.category}</div>
                        <div className="text-sm text-red-700 mt-1">{w.description}</div>
                        <div className="text-xs text-red-600 mt-1">{w.evidence}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="text-xs text-gray-400">
                分析日時: {analysis.strength_weakness?.analyzed_at
                  ? new Date(analysis.strength_weakness.analyzed_at).toLocaleString("ja-JP")
                  : ""}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">分析結果がありません。「AI分析実行」ボタンで分析を実行してください。</p>
          )}
        </div>

        {/* 口コミスコア推移 */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">口コミスコア推移</h3>
          {reviews.length > 0 ? (
            <ReviewChart reviews={reviews} />
          ) : (
            <p className="text-sm text-gray-500">口コミデータがありません</p>
          )}
        </div>

        {/* 最新ニュース */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">最新ニュース</h3>
          {news.length === 0 ? (
            <p className="text-sm text-gray-500">ニュースがありません</p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {news.map((item) => (
                <div key={item.id} className="border-b border-gray-100 pb-2 last:border-0">
                  <div className="flex items-center gap-2 mb-1">
                    {item.impact_score && (
                      <span className={`text-xs px-1.5 py-0.5 rounded ${IMPACT_COLORS[item.impact_score] || ""}`}>
                        {item.impact_score}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">{item.source}</span>
                  </div>
                  <div className="text-sm text-gray-900">{item.title}</div>
                  {item.summary && <div className="text-xs text-gray-500 mt-1 line-clamp-2">{item.summary}</div>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 採用動向 */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            採用動向
            <span className="text-sm font-normal text-gray-500 ml-2">{jobs.length}件</span>
          </h3>
          {jobs.length === 0 ? (
            <p className="text-sm text-gray-500">求人情報がありません</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {jobs.map((job) => (
                <div key={job.id} className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-gray-900">{job.title}</div>
                  <div className="flex items-center gap-3 mt-1">
                    {job.department && <span className="text-xs text-gray-500">{job.department}</span>}
                    {job.salary_range && <span className="text-xs text-emerald-600">{job.salary_range}</span>}
                    <span className="text-xs text-gray-400">{job.source}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
