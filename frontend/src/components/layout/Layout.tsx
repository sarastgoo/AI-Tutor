import { Link, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { path: "/", label: "Library", icon: "📚" },
  { path: "/tutor", label: "Tutor", icon: "💬" },
  { path: "/vocabulary", label: "Vocabulary", icon: "📖" },
  { path: "/progress", label: "Progress", icon: "📊" },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-6">
          <Link to="/" className="font-bold text-lg">
            AI English Tutor
          </Link>
          <div className="flex gap-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  location.pathname === item.path
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent",
                )}
              >
                {item.icon} {item.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}