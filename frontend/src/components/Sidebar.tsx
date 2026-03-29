"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { companiesApi } from "@/lib/api";
import { Company } from "@/types";

const navItems = [
  { href: "/", label: "業界オーバービュー", icon: "📊" },
  { href: "/compare", label: "企業比較", icon: "⚖️" },
  { href: "/alerts", label: "アラート", icon: "🔔" },
];

const adminItems = [
  { href: "/admin", label: "管理画面", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);

  useEffect(() => {
    companiesApi.list({ is_active: true }).then(setCompanies).catch(() => {});
  }, []);

  const items = user?.role === "admin" ? [...navItems, ...adminItems] : navItems;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-700">競合ナビ</h1>
        <p className="text-xs text-gray-500 mt-1">Competitive Intelligence</p>
      </div>
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              pathname === item.href
                ? "bg-primary-50 text-primary-700 font-medium"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}

        {/* 企業一覧 */}
        {companies.length > 0 && (
          <>
            <div className="text-xs text-gray-400 uppercase tracking-wide mt-4 mb-1 px-3">企業</div>
            {companies.map((c) => (
              <Link
                key={c.id}
                href={`/companies/${c.id}`}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  pathname === `/companies/${c.id}`
                    ? "bg-primary-50 text-primary-700 font-medium"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                {c.name}
              </Link>
            ))}
          </>
        )}
      </nav>
      {user && (
        <div className="p-4 border-t border-gray-200">
          <div className="text-sm text-gray-700 font-medium">{user.name}</div>
          <div className="text-xs text-gray-500">{user.email}</div>
          <button
            onClick={logout}
            className="mt-2 text-xs text-red-500 hover:text-red-700"
          >
            ログアウト
          </button>
        </div>
      )}
    </aside>
  );
}
