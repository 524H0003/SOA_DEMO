import { useEffect, useState } from "react";
import { AbsentRequestForm } from "./components/absent-request-form";
import { AbsentRequestList } from "./components/absent-request-list";
import { listAbsentRequests, type AbsentRequest } from "./lib/api";

export default function App() {
  const [employeeName, setEmployeeName] = useState(
    () => window.localStorage.getItem("absent.employeeName") ?? "",
  );
  const [requests, setRequests] = useState<AbsentRequest[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = () =>
    listAbsentRequests()
      .then(setRequests)
      .catch(() => setNotice("Không thể tải trạng thái từ API."));
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(timer);
  }, []);

  const handleCreated = (request: AbsentRequest) => {
    setNotice(`Đã gửi yêu cầu vắng mặt tới ${request.manager_email}.`);
    void refresh();
  };

  if (!employeeName)
    return (
      <main className="shell login-shell">
        <section className="login-panel">
          <span className="eyebrow">Employee self-service</span>
          <h1>Absent Desk</h1>
          <p>Nhập tên nhân viên để bắt đầu phiên thử nghiệm.</p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const name =
                new FormData(event.currentTarget)
                  .get("employee_name")
                  ?.toString()
                  .trim() ?? "";
              if (name.length >= 2) {
                window.localStorage.setItem("absent.employeeName", name);
                setEmployeeName(name);
              }
            }}
          >
            <label className="field-label" htmlFor="employee-name">
              Tên nhân viên
            </label>
            <input
              className="input"
              id="employee-name"
              name="employee_name"
              minLength={2}
              required
              autoFocus
              placeholder="Nguyễn Văn An"
            />
            <button className="button" type="submit">
              Vào trang yêu cầu
            </button>
          </form>
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
          Phiên thử nghiệm: {employeeName}. Gửi yêu cầu trong vài phút và theo
          dõi quyết định từ email quản lý.
        </p>
      </section>
      {notice && <div className="notice">{notice}</div>}
      <div className="content-grid">
        <AbsentRequestForm
          employeeName={employeeName}
          onCreated={handleCreated}
        />
        <AbsentRequestList requests={requests} />
      </div>
      <footer>Powered by FastAPI · Gmail Watch · SQLite</footer>
    </main>
  );
}
