import { useForm } from "@tanstack/react-form";
import { z } from "zod";
import { createAbsentRequest, type AbsentRequestPayload } from "../lib/api";
import { FieldLabel, Input, Textarea } from "./ui";

const schema = z.object({
  employee_name: z.string().min(2, "Nhập họ tên nhân viên"),
  employee_email: z.string().email("Email nhân viên không hợp lệ"),
  manager_email: z.string().email("Email quản lý không hợp lệ"),
  absent_type: z.string().min(2, "Chọn loại vắng mặt"),
  start_date: z.string().min(1, "Chọn ngày bắt đầu"),
  end_date: z.string().min(1, "Chọn ngày kết thúc"),
  reason: z.string().min(5, "Lý do cần ít nhất 5 ký tự"),
}).refine((value) => value.end_date >= value.start_date, {
  message: "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu",
  path: ["end_date"],
});

type FormValues = z.infer<typeof schema>;

function errorText(errors: unknown[]) {
  return errors.length > 0 ? String(errors[0]) : null;
}

export function AbsentRequestForm({ onCreated }: { onCreated: (request: AbsentRequestPayload) => void }) {
  const form = useForm({
    defaultValues: {
      employee_name: "",
      employee_email: "",
      manager_email: "",
      absent_type: "Annual",
      start_date: "",
      end_date: "",
      reason: "",
    } satisfies FormValues,
    onSubmit: async ({ value }) => {
      const parsed = schema.safeParse(value);
      if (!parsed.success) {
        throw new Error(parsed.error.issues[0]?.message ?? "Dữ liệu không hợp lệ");
      }
      const result = await createAbsentRequest(parsed.data);
      onCreated(result);
      form.reset();
    },
  });

  return (
    <form className="absent-form" onSubmit={(event) => { event.preventDefault(); event.stopPropagation(); void form.handleSubmit(); }}>
      <div className="form-heading">
        <span className="eyebrow">New request</span>
        <h2>Gửi yêu cầu vắng mặt</h2>
        <p>Quản lý sẽ nhận email và phản hồi trực tiếp bằng Gmail.</p>
      </div>
      <div className="form-grid">
        <form.Field name="employee_name" validators={{ onChange: ({ value }) => value.length < 2 ? "Nhập họ tên nhân viên" : undefined }}>
          {(field) => <div><FieldLabel>Họ tên</FieldLabel><Input value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} placeholder="Nguyễn Văn An" />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
        </form.Field>
        <form.Field name="employee_email" validators={{ onChange: ({ value }) => !z.string().email().safeParse(value).success ? "Email không hợp lệ" : undefined }}>
          {(field) => <div><FieldLabel>Email nhân viên</FieldLabel><Input type="email" value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} placeholder="ban@congty.vn" />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
        </form.Field>
        <form.Field name="manager_email" validators={{ onChange: ({ value }) => !z.string().email().safeParse(value).success ? "Email không hợp lệ" : undefined }}>
          {(field) => <div><FieldLabel>Email quản lý</FieldLabel><Input type="email" value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} placeholder="manager@congty.vn" />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
        </form.Field>
        <form.Field name="absent_type">
          {(field) => <div><FieldLabel>Loại vắng mặt</FieldLabel><select className="input" value={field.state.value} onChange={(event) => field.handleChange(event.target.value)}><option>Annual</option><option>Sick</option><option>Personal</option></select></div>}
        </form.Field>
        <form.Field name="start_date" validators={{ onChange: ({ value }) => !value ? "Chọn ngày bắt đầu" : undefined }}>
          {(field) => <div><FieldLabel>Từ ngày</FieldLabel><Input type="date" value={field.state.value} onChange={(event) => field.handleChange(event.target.value)} />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
        </form.Field>
        <form.Field name="end_date" validators={{ onChange: ({ value }) => !value ? "Chọn ngày kết thúc" : undefined }}>
          {(field) => <div><FieldLabel>Đến ngày</FieldLabel><Input type="date" value={field.state.value} onChange={(event) => field.handleChange(event.target.value)} />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
        </form.Field>
      </div>
      <form.Field name="reason" validators={{ onChange: ({ value }) => value.length < 5 ? "Lý do cần ít nhất 5 ký tự" : undefined }}>
        {(field) => <div><FieldLabel>Lý do</FieldLabel><Textarea rows={4} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} placeholder="Mô tả ngắn gọn lý do vắng mặt..." />{errorText(field.state.meta.errors) && <span className="error">{errorText(field.state.meta.errors)}</span>}</div>}
      </form.Field>
      <form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
        {([canSubmit, isSubmitting]) => <button className="button" type="submit" disabled={!canSubmit || isSubmitting}>{isSubmitting ? "Đang gửi..." : "Gửi yêu cầu"}</button>}
      </form.Subscribe>
    </form>
  );
}
