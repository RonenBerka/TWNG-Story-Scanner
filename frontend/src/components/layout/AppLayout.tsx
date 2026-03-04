import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../../lib/auth";
import "../../styles/layout.css";

const stages = [
  { to: "/scanner", label: "Scanner", num: 1 },
  { to: "/extraction", label: "Extraction", num: 2 },
  { to: "/approval", label: "Pre-Claim", num: 3 },
  { to: "/claims", label: "Claims", num: 4 },
];

export default function AppLayout() {
  const { logout } = useAuth();

  return (
    <div className="app-layout">
      <nav className="app-nav">
        <div className="app-nav-left">
          <span className="app-logo">TWNG</span>
          <div className="stage-tabs">
            {stages.map((s) => (
              <NavLink
                key={s.to}
                to={s.to}
                className={({ isActive }) =>
                  `stage-tab${isActive ? " active" : ""}`
                }
              >
                <span className="stage-num">{s.num}</span>
                {s.label}
              </NavLink>
            ))}
          </div>
        </div>
        <button className="app-logout" onClick={logout}>
          Logout
        </button>
      </nav>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
