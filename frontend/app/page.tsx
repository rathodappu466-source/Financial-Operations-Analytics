export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-[#020817] text-white p-10">

      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-5xl font-bold">Account Holder Profile</h1>
          <p className="text-gray-400 mt-2">
            Enterprise Financial Intelligence Account
          </p>
        </div>

        <div className="bg-blue-600 px-6 py-3 rounded-2xl shadow-lg">
          <p className="font-semibold">Premium Enterprise Plan</p>
        </div>
      </div>

      {/* Profile Card */}
      <div className="bg-[#0F172A] rounded-3xl p-8 shadow-2xl border border-gray-800">

        <div className="flex items-center gap-6">

          <div className="w-28 h-28 rounded-full bg-blue-600 flex items-center justify-center text-4xl font-bold">
            A
          </div>

          <div>
            <h2 className="text-3xl font-bold">Appu Rathod</h2>

            <p className="text-gray-400 mt-1">
              Senior Financial Operations Analyst
            </p>

            <p className="text-gray-500 mt-2">
              FinAnalytics Enterprise Solutions Pvt Ltd
            </p>
          </div>
        </div>

        {/* Details Grid */}

        <div className="grid grid-cols-2 gap-6 mt-10">

          <div className="bg-[#111827] p-5 rounded-2xl">
            <p className="text-gray-400">Email Address</p>
            <h3 className="text-xl font-semibold mt-2">
              appu@finanalytics.ai
            </h3>
          </div>

          <div className="bg-[#111827] p-5 rounded-2xl">
            <p className="text-gray-400">Department</p>
            <h3 className="text-xl font-semibold mt-2">
              Financial Intelligence
            </h3>
          </div>

          <div className="bg-[#111827] p-5 rounded-2xl">
            <p className="text-gray-400">Employee ID</p>
            <h3 className="text-xl font-semibold mt-2">
              FIN-2026-991
            </h3>
          </div>

          <div className="bg-[#111827] p-5 rounded-2xl">
            <p className="text-gray-400">Location</p>
            <h3 className="text-xl font-semibold mt-2">
              Bengaluru, India
            </h3>
          </div>

        </div>

      </div>

      {/* Activity Section */}

      <div className="grid grid-cols-3 gap-6 mt-10">

        <div className="bg-[#0F172A] p-6 rounded-3xl border border-gray-800">
          <h2 className="text-gray-400">Predictions Generated</h2>
          <p className="text-5xl font-bold mt-4">1,284</p>
        </div>

        <div className="bg-[#0F172A] p-6 rounded-3xl border border-gray-800">
          <h2 className="text-gray-400">Customer Retention Rate</h2>
          <p className="text-5xl font-bold mt-4">91%</p>
        </div>

        <div className="bg-[#0F172A] p-6 rounded-3xl border border-gray-800">
          <h2 className="text-gray-400">AI Model Accuracy</h2>
          <p className="text-5xl font-bold mt-4">79%</p>
        </div>

      </div>

    </div>
  );
}