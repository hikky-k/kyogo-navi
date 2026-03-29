"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ReviewData {
  overall_score: number;
  source: string;
  review_count: number;
  scraped_at: string;
}

export default function ReviewChart({ reviews }: { reviews: ReviewData[] }) {
  const chartData = reviews.map((r) => ({
    date: new Date(r.scraped_at).toLocaleDateString("ja-JP", { month: "short", day: "numeric" }),
    score: r.overall_score,
    source: r.source,
    reviews: r.review_count,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
            formatter={(value: number) => [value.toFixed(1), "スコア"]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4 }}
            name="総合スコア"
          />
        </LineChart>
      </ResponsiveContainer>
      {/* 最新スコア表示 */}
      {reviews.length > 0 && (
        <div className="mt-3 flex items-center gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600">
              {reviews[reviews.length - 1].overall_score.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">最新スコア</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-700">
              {reviews[reviews.length - 1].review_count}
            </div>
            <div className="text-xs text-gray-500">レビュー数</div>
          </div>
        </div>
      )}
    </div>
  );
}
