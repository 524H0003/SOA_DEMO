import { useEffect, useState } from "react";
import { LeaveRequestForm } from "./components/leave-request-form";
import { LeaveRequestList } from "./components/leave-request-list";
import { listLeaveRequests, type LeaveRequest, type LeaveRequestPayload } from "./lib/api";

export default function App() {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = () => listLeaveRequests().then(setRequests).catch(() => setNotice("Không thể tải trạng thái từ API."));
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 10000); return () => window.clearInterval(timer); }, []);

  const handleCreated = (request: LeaveRequestPayload) => {
    setNotice(`Đã gửi yêu cầu nghỉ phép tới ${request.manager_email}.`);
    void refresh();
  };

  return <main className="shell"><header className="topbar"><div className="brand-mark">LD</div><div><span className="eyebrow">People operations</span><h1>Leave Desk</h1></div><div className="sync-indicator"><span className="pulse" /> Gmail sync active</div></header><section className="intro"><div><span className="eyebrow">Employee self-service</span><h2>Một ngày nghỉ,<br /><em>một quy trình rõ ràng.</em></h2></div><p>Gửi yêu cầu trong vài phút. Mọi quyết định được xử lý từ email quản lý và đồng bộ ngược về đây.</p></section>{notice && <div className="notice">{notice}</div>}<div className="content-grid"><LeaveRequestForm onCreated={handleCreated} /><LeaveRequestList requests={requests} /></div><footer>Powered by FastAPI · Gmail Watch · SQLite</footer></main>;
}
