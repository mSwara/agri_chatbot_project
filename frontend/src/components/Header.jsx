export default function Header() {
  return (
    <header className="flex items-center gap-3 px-4 py-3 bg-agri-700 text-white shadow-md shrink-0">
      <span className="text-2xl">🌾</span>
      <div>
        <h1 className="font-semibold text-lg leading-tight">AgriBot</h1>
        <p className="text-xs text-agri-100/90">AI-Powered Agricultural Assistant</p>
      </div>
    </header>
  );
}
