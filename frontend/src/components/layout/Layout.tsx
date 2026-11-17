import { Link, Outlet, useLocation, useSearchParams } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { path: "/", label: "Library", icon: "📚" },
  { path: "/tutor", label: "Tutor", icon: "💬" },
  { path: "/vocabulary", label: "Vocabulary", icon: "📖" },
  { path: "/speaking", label: "Speaking", icon: "🎤" },
  { path: "/progress", label: "Progress", icon: "📊" },
];

export default function Layout() {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const bookId = searchParams.get("book");

  // اگر در صفحه Library یا Progress هستیم، پارامتر book را نگه نمی‌داریم.
  // در غیر این صورت، آن را به لینک‌ها اضافه می‌کنیم تا انتخاب کتاب حفظ شود.
  const preserveBook = bookId && location.pathname !== "/" && location.pathname !== "/progress";

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-6">
          <Link to="/" className="font-bold text-lg">
            AI English Tutor
          </Link>
          <div className="flex gap-2">
            {NAV_ITEMS.map((item) => {
              // برای هر آیتم، اگر باید book را حفظ کنیم، به URL اضافه می‌کنیم
              const to =
                preserveBook && item.path !== "/"
                  ? `${item.path}?book=${bookId}`
                  : item.path;
              return (
                <Link
                  key={item.path}
                  to={to}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    location.pathname === item.path
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent",
                  )}
                >
                  {item.icon} {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}