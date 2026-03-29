"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { companiesApi, crawlSourcesApi, crawlApi } from "@/lib/api";
import { Company, CrawlSource } from "@/types";

const CATEGORIES = ["総合系", "IT系", "ブティック系"];
const SOURCE_TYPES = [
  { value: "official", label: "公式サイト" },
  { value: "news", label: "ニュースサイト" },
  { value: "review", label: "口コミサイト" },
  { value: "job", label: "求人サイト" },
];

export default function AdminPage() {
  const { user } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [sources, setSources] = useState<CrawlSource[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [crawlMessage, setCrawlMessage] = useState("");
  const [crawling, setCrawling] = useState(false);

  // 企業フォーム
  const [companyForm, setCompanyForm] = useState({
    name: "",
    category: "総合系",
    website_url: "",
    description: "",
  });
  const [editingCompanyId, setEditingCompanyId] = useState<number | null>(null);

  // ソースフォーム
  const [sourceForm, setSourceForm] = useState({
    source_type: "official",
    url: "",
    crawl_frequency: "daily",
  });

  // データ取得
  const fetchCompanies = async () => {
    try {
      const data = await companiesApi.list();
      setCompanies(data);
    } catch {
      setError("企業一覧の取得に失敗しました");
    }
  };

  const fetchSources = async (companyId: number) => {
    try {
      const data = await crawlSourcesApi.list(companyId);
      setSources(data);
    } catch {
      setError("ソース一覧の取得に失敗しました");
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  useEffect(() => {
    if (selectedCompanyId) fetchSources(selectedCompanyId);
  }, [selectedCompanyId]);

  if (user?.role !== "admin") {
    return (
      <div className="text-red-600 p-8">管理者権限が必要です</div>
    );
  }

  // 企業登録・更新
  const handleCompanySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (editingCompanyId) {
        await companiesApi.update(editingCompanyId, companyForm);
        setEditingCompanyId(null);
      } else {
        await companiesApi.create(companyForm);
      }
      setCompanyForm({ name: "", category: "総合系", website_url: "", description: "" });
      fetchCompanies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存に失敗しました");
    }
  };

  const handleEditCompany = (company: Company) => {
    setEditingCompanyId(company.id);
    setCompanyForm({
      name: company.name,
      category: company.category,
      website_url: company.website_url || "",
      description: company.description || "",
    });
  };

  const handleDeleteCompany = async (id: number) => {
    if (!confirm("この企業を削除しますか？関連するデータも全て削除されます。")) return;
    try {
      await companiesApi.delete(id);
      if (selectedCompanyId === id) setSelectedCompanyId(null);
      fetchCompanies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "削除に失敗しました");
    }
  };

  // ソース登録
  const handleSourceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId) return;
    setError("");
    try {
      await crawlSourcesApi.create({
        company_id: selectedCompanyId,
        ...sourceForm,
      });
      setSourceForm({ source_type: "official", url: "", crawl_frequency: "daily" });
      fetchSources(selectedCompanyId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ソースの登録に失敗しました");
    }
  };

  const handleDeleteSource = async (id: number) => {
    if (!confirm("このソースを削除しますか？")) return;
    try {
      await crawlSourcesApi.delete(id);
      if (selectedCompanyId) fetchSources(selectedCompanyId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "削除に失敗しました");
    }
  };

  // クロール実行
  const handleCrawlSource = async (sourceId: number) => {
    setCrawling(true);
    setCrawlMessage("");
    setError("");
    try {
      const res = await crawlApi.runSingle(sourceId);
      if (res.success) {
        setCrawlMessage(`クロール成功: ${res.items_count}件取得`);
      } else {
        setError(`クロール失敗: ${res.error}`);
      }
      if (selectedCompanyId) fetchSources(selectedCompanyId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "クロール実行に失敗しました");
    } finally {
      setCrawling(false);
    }
  };

  const handleCrawlAll = async () => {
    if (!selectedCompanyId) return;
    setCrawling(true);
    setCrawlMessage("");
    setError("");
    try {
      const res = await crawlApi.runAll(selectedCompanyId);
      setCrawlMessage(`一括クロール完了: 成功=${res.total_success}, 失敗=${res.total_failure}`);
      fetchSources(selectedCompanyId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "一括クロール実行に失敗しました");
    } finally {
      setCrawling(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">管理画面</h2>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
          {error}
        </div>
      )}
      {crawlMessage && (
        <div className="bg-green-50 text-green-700 text-sm p-3 rounded-lg mb-4">
          {crawlMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 企業管理 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">企業管理</h3>

          {/* 企業登録フォーム */}
          <form onSubmit={handleCompanySubmit} className="bg-white p-4 rounded-xl border border-gray-200 mb-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">企業名</label>
              <input
                type="text"
                value={companyForm.name}
                onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ</label>
              <select
                value={companyForm.category}
                onChange={(e) => setCompanyForm({ ...companyForm, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">WebサイトURL</label>
              <input
                type="url"
                value={companyForm.website_url}
                onChange={(e) => setCompanyForm({ ...companyForm, website_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">説明</label>
              <textarea
                value={companyForm.description}
                onChange={(e) => setCompanyForm({ ...companyForm, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
            <div className="flex gap-2">
              <button type="submit" className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">
                {editingCompanyId ? "更新" : "登録"}
              </button>
              {editingCompanyId && (
                <button
                  type="button"
                  onClick={() => {
                    setEditingCompanyId(null);
                    setCompanyForm({ name: "", category: "総合系", website_url: "", description: "" });
                  }}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-300"
                >
                  キャンセル
                </button>
              )}
            </div>
          </form>

          {/* 企業一覧 */}
          <div className="space-y-2">
            {companies.map((company) => (
              <div
                key={company.id}
                className={`bg-white p-4 rounded-xl border cursor-pointer transition-colors ${
                  selectedCompanyId === company.id
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => setSelectedCompanyId(company.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900">{company.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      <span className="bg-gray-100 px-2 py-0.5 rounded">{company.category}</span>
                      {!company.is_active && (
                        <span className="bg-red-100 text-red-600 px-2 py-0.5 rounded ml-1">無効</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleEditCompany(company); }}
                      className="text-xs text-primary-600 hover:text-primary-800 px-2 py-1"
                    >
                      編集
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteCompany(company.id); }}
                      className="text-xs text-red-500 hover:text-red-700 px-2 py-1"
                    >
                      削除
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {companies.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">企業が登録されていません</p>
            )}
          </div>
        </div>

        {/* クロールソース管理 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">クロールソース設定</h3>

          {selectedCompanyId ? (
            <>
              <form onSubmit={handleSourceSubmit} className="bg-white p-4 rounded-xl border border-gray-200 mb-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ソースタイプ</label>
                  <select
                    value={sourceForm.source_type}
                    onChange={(e) => setSourceForm({ ...sourceForm, source_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                  >
                    {SOURCE_TYPES.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                  <input
                    type="url"
                    value={sourceForm.url}
                    onChange={(e) => setSourceForm({ ...sourceForm, url: e.target.value })}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">収集頻度</label>
                  <select
                    value={sourceForm.crawl_frequency}
                    onChange={(e) => setSourceForm({ ...sourceForm, crawl_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                  >
                    <option value="daily">毎日</option>
                    <option value="weekly">毎週</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <button type="submit" className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">
                    ソース追加
                  </button>
                  <button
                    type="button"
                    onClick={handleCrawlAll}
                    disabled={crawling || sources.length === 0}
                    className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {crawling ? "実行中..." : "一括クロール"}
                  </button>
                </div>
              </form>

              <div className="space-y-2">
                {sources.map((source) => (
                  <div key={source.id} className="bg-white p-3 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {SOURCE_TYPES.find((s) => s.value === source.source_type)?.label || source.source_type}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 truncate max-w-xs">{source.url}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          頻度: {source.crawl_frequency === "daily" ? "毎日" : "毎週"}
                          {source.last_crawled_at && ` | 最終: ${new Date(source.last_crawled_at).toLocaleDateString("ja-JP")}`}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleCrawlSource(source.id)}
                          disabled={crawling}
                          className="text-xs text-emerald-600 hover:text-emerald-800 px-2 py-1 disabled:opacity-50"
                        >
                          {crawling ? "..." : "実行"}
                        </button>
                        <button
                          onClick={() => handleDeleteSource(source.id)}
                          className="text-xs text-red-500 hover:text-red-700 px-2 py-1"
                        >
                          削除
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {sources.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">ソースが登録されていません</p>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white p-6 rounded-xl border border-gray-200 text-center">
              <p className="text-sm text-gray-500">左の企業一覧から企業を選択してください</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
