"use client";

import {
  LayoutDashboard,
  User,
  History,
  BarChart3,
  LogOut
} from "lucide-react";

export default function Sidebar() {
  return (
    <div className="w-[260px] h-screen bg-[#0B1220] border-r border-gray-800 p-6 fixed">

      <h1 className="text-2xl font-bold text-blue-500 mb-10">
        FinAnalytics
      </h1>

      <div className="space-y-4">

        <button className="flex items-center gap-3 w-full p-4 rounded-xl bg-blue-600 hover:bg-blue-700 transition">
          <LayoutDashboard size={20} />
          Dashboard
        </button>

        <button className="flex items-center gap-3 w-full p-4 rounded-xl hover:bg-[#111827] transition">
          <User size={20} />
          Profile
        </button>

        <button className="flex items-center gap-3 w-full p-4 rounded-xl hover:bg-[#111827] transition">
          <History size={20} />
          History
        </button>

        <button className="flex items-center gap-3 w-full p-4 rounded-xl hover:bg-[#111827] transition">
          <BarChart3 size={20} />
          Analytics
        </button>

      </div>

      <button className="absolute bottom-10 left-6 flex items-center gap-3 bg-red-600 hover:bg-red-700 px-5 py-3 rounded-xl transition">
        <LogOut size={18} />
        Logout
      </button>

    </div>
  );
}