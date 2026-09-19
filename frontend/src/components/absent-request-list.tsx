import type { AbsentRequest } from "../lib/api";

const statusLabels = { pending: "Đang chờ", approved: "Đã duyệt", rejected: "Từ chối" };

export function AbsentRequestList({ requests }: { requests: AbsentRequest[] }) {
  return <section className="request-panel"><div className="section-heading"><div><span className="eyebrow">Live status</span><h2>Trạng thái yêu cầu</h2></div><span className="count">{requests.length} đơn</span></div>{requests.length === 0 ? <p className="empty">Chưa có yêu cầu nào.</p> : <div className="request-list">{requests.map((request) => <article className="request-row" key={request.id}><div className="request-id">AR-{request.id.toString().padStart(3, "0")}</div><div className="request-main"><strong>{request.employee_name}</strong><span>{request.absent_type} · {request.start_date} → {request.end_date}</span></div><span className={`status status-${request.status}`}>{statusLabels[request.status]}</span></article>)}</div>}</section>;
}
