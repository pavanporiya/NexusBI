export default function DashboardHome() {
  return (
    <main className="flex-1 flex flex-col justify-center items-center p-8">
      <div className="max-w-md w-full bg-[#18181b] border border-[#27272a] rounded-lg p-6 text-center space-y-4">
        <h1 className="text-2xl font-bold tracking-tight text-white font-outfit">
          NexusBI Platform
        </h1>
        <p className="text-[#a1a1aa] font-inter text-sm">
          Welcome to the NexusBI Enterprise Analytics Platform. The architecture
          foundation is active.
        </p>
        <div className="pt-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
            System Online
          </span>
        </div>
      </div>
    </main>
  );
}
