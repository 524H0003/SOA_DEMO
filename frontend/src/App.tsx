import { useEffect, useState } from "react";
import { AbsentRequestForm } from "./components/absent-request-form";
import { AbsentRequestList } from "./components/absent-request-list";
import { listAbsentRequests, login, type AbsentRequest } from "./lib/api";

export default function App() {
  const [username, setUsername] = useState(
    () => window.localStorage.getItem("absent.username") ?? "",
  );
  const [requests, setRequests] = useState<AbsentRequest[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const refresh = () =>
    listAbsentRequests()
      .then(setRequests)
      .catch(() => setNotice("Không thể tải trạng thái từ API."));
  useEffect(() => {
    if (!username) return;
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(timer);
  }, [username]);

  const handleCreated = (request: AbsentRequest) => {
    setNotice(`Đã gửi yêu cầu vắng mặt tới ${request.manager_email}.`);
    void refresh();
  };

  if (!username)
    return (
      <main className="shell login-shell">
        <section className="login-panel" aria-labelledby="login-title">
          <div className="login-brand">
            <div className="brand-mark">AD</div>
            <span className="eyebrow">People operations</span>
          </div>
          <h1 id="login-title">Chào mừng trở lại.</h1>
          <p>Đăng nhập để gửi và theo dõi yêu cầu vắng mặt của bạn.</p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              const name = form.get("username")?.toString().trim() ?? "";
              const password = form.get("password")?.toString() ?? "";
              setLoginError(null);
              setIsLoggingIn(true);
              void login({ username: name, password })
                .then(({ access_token }) => {
                  window.localStorage.setItem("absent.accessToken", access_token);
                  window.localStorage.setItem("absent.username", name);
                  setUsername(name);
                })
                .catch((error: Error) => setLoginError(error.message))
                .finally(() => setIsLoggingIn(false));
            }}
          >
            <label className="field-label" htmlFor="employee-name">
              Tên đăng nhập
            </label>
            <input
              className="input"
              id="employee-name"
              name="username"
              minLength={3}
              required
              autoFocus
              autoComplete="username"
              placeholder="nguyen.van.an"
            />
            <label className="field-label login-password-label" htmlFor="password">
              Mật khẩu
            </label>
            <input
              className="input"
              id="password"
              name="password"
              minLength={8}
              required
              type="password"
              autoComplete="current-password"
              placeholder="Nhập mật khẩu của bạn"
            />
            {loginError && <p className="login-error" role="alert">{loginError}</p>}
            <button className="button" type="submit" disabled={isLoggingIn}>
              {isLoggingIn ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>
          <span className="login-footer">Absent Desk · Internal workspace</span>
        </section>
      </main>
    );
  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark">AD</div>
        <div>
          <span className="eyebrow">People operations</span>
          <h1>Absent Desk</h1>
        </div>
        <div className="sync-indicator">
          <span className="pulse" /> Gmail sync active
        </div>
      </header>
      <section className="intro">
        <div>
          <span className="eyebrow">Employee self-service</span>
          <h2>
            Một ngày vắng mặt,
            <br />
            <em>một quy trình rõ ràng.</em>
          </h2>
        </div>
        <p>
          Xin chào {username}. Gửi yêu cầu trong vài phút và theo
          dõi quyết định từ email quản lý.
        </p>
      </section>
      {notice && <div className="notice">{notice}</div>}
      <div className="content-grid">
        <AbsentRequestForm
          employeeName={username}
          onCreated={handleCreated}
        />
        <AbsentRequestList requests={requests} />
      </div>
      <footer>Powered by FastAPI · Gmail Watch · SQLite</footer>
    </main>
  );
}
