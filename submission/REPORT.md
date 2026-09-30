# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đào Minh Hiếu
- **MSSV:** 2A202602561
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/hieujinx/K4-L3B-Day13-DaoMinhHieu-2A202602561-Monitoring-LLMOps
- **Commit SHA cuối:** Dùng SHA của `origin/main` được nộp kèm URL repository trên LMS/Codelabs.
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602561`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt promote | `evidence/10a-prompt-promote.png` |
| Prompt rollback | `evidence/10b-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (20 records; 0 correlation ID; 0 PII leak) | 100/100 (54 records; 27 correlation IDs; 0 PII leak) | CP1 đạt đủ schema, correlation ID, enrichment và scrub PII |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Dashboard contract hợp lệ; panel Errors tính retrieval success trên mọi event có `tool_success` |
| `pytest` | 22 passed | 24 passed | Chạy bằng Python 3.11.9 trong `.venv`; CP1 bổ sung test CCCD/thẻ |
| Số traces hợp lệ | 0 | 10 | 5 trace dùng v1/`baseline`, 5 trace dùng v2/`candidate`; có child `retrieval` và `generation` |
| Số PII leak | 0 | 0 | Validator không phát hiện PII thô; payload preview đã che PII |
| Latency P95 / TTFT P95 | 151 ms / 50 ms (ứng dụng) | 2654.8 ms / 50 ms (challenge) | Retrieval incident làm tăng tail latency, TTFT không đổi |
| Retrieval success rate | 100% (10/10) | 100% trong incident chậm | Retrieval hoàn thành nhưng chậm, không phải lỗi tool |

> Kiểm tra CP0 sau khi cấu hình `.env`: Python 3.11.9, `pip check` không có lỗi, `/health` trả `ok: true` và `tracing_enabled: true`, dashboard validator 6/6. Sau CP2, prompt managed v1/v2 đã được tạo và workload evidence dùng prompt từ Langfuse thay vì local fallback.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context cũ, nhận `x-request-id` nếu đúng dạng `req-<8-hex>`, nếu không thì sinh ID mới bằng `secrets.token_hex(4)`. ID được bind vào structlog contextvars, gắn vào request state và trả lại qua `x-request-id`/response body.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env` được bind trước `request_received`; correlation ID xuất hiện trong cả request và response event.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` được đăng ký trước file writer và JSON renderer; scrub đệ quy mọi string trong event dict, gồm email, điện thoại Việt Nam, CCCD và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** `validate_logs.py` đạt 100/100, 0 PII leak; request thử nghiệm trả `x-request-id=req-a1b2c3d4`, `x-response-time-ms` và body có cùng correlation ID.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project `day13-k4-l3b-2A202602561` có 10 trace của hai session `day13-evidence-baseline` và `day13-evidence-candidate`; các correlation ID tương ứng có trong structured log.
- **Cấu trúc root/retrieval/generation observations:** `day13-agent-request` → `lab-agent-run` → `retrieval` (retriever) và `generation` (generation). Hai child đều không capture raw input/output; generation cập nhật model, `usage_details`, `cost_details` và nhận managed prompt object khi prompt tồn tại.
- **Cách nối trace với log:** Dùng `correlation_id` trong metadata trace và cùng field trong `request_received`/`response_sent`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** v1, labels `baseline` và `production` sau rollback; trace mẫu `b0df7b9381214eeae29b58f528a316e1`, correlation ID `req-b1000004`.
- **Version/label candidate:** v2, label `candidate`; trace mẫu `818792d42fadd381b2faf303ec74af59`, correlation ID `req-c2000004`.
- **Trace IDs baseline:** `b0df7b9381214eeae29b58f528a316e1`, `e458551a02abe0e1f9a998601bf46d50`, `74d1581e8f5025dd5ae00eb6ff129596`, `bd890cd0ab9be171fbf4e736c91de021`, `ed0a31ceb20956ca6c1eb0ab6e815b94`.
- **Trace IDs candidate:** `818792d42fadd381b2faf303ec74af59`, `a1582d356cf5c4794849b0cc202f9421`, `16c968401ce62a3f35dde4198e1b151a`, `0d4718f353881e76ed89d39ff2c86fea`, `8808f78091e584d2d4ff11dbb0b4d33f`.
- **Cách promote và rollback `production`:** `scripts/setup_prompts.py` đã chuyển `production` sang v2 để promote rồi chuyển về v1 để rollback. Trạng thái cuối: v1 có `baseline, production`; v2 có `candidate`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `scripts/dashboard.py` đọc `data/logs.jsonl` và tạo `submission/evidence/dashboard.html` với 6 panel Latency, Traffic, Errors, Cost, Tokens, Quality; time range 60 phút, refresh 30 giây và threshold cho từng panel. Contract validator đạt 6/6.
- **SLO và lý do chọn:** `fast_successful_requests`, 99.5% request thành công và latency không quá 3000ms trong cửa sổ 28 ngày; baseline CP1 thấp hơn ngưỡng này.
- **Cách tính error budget:** 100% - 99.5% = 0.5%; với 10,000 request, tối đa 50 request không đạt SLO.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (P95 > 3000ms/5m), `ElevatedErrorRate` (>2%/5m), `LowRetrievalSuccess` (<90%/10m); runbook nằm tại `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30T10:13:22Z`–`2026-09-30T10:13:36Z` (UTC), theo `data/logs.jsonl`.
- **Triệu chứng từ metrics:** Baseline challenge queries có latency trung bình `305 ms` nếu tính cả 5 baseline request; riêng challenge incident có trung bình `2653.2 ms` và P95 `2654.8 ms`, vượt threshold `2000 ms` ở cả 5/5 response. TTFT challenge giữ ở `50 ms`, error rate `0%`, retrieval success `100%`.
- **Log line và correlation ID liên quan:** Event `response_sent` của `req-5170bf64` có `latency_ms=2655`, `ttft_ms=50`, `tool_name=retrieval`, `tool_success=true`, `session_id=k4-l3b-challenge-s03`. Các request incident còn lại: `req-114d5d26`, `req-b1ffbf9f`, `req-d5a6b380`, `req-5a181a3f`.
- **Trace ID và span gây ảnh hưởng:** Trace `f70e11ff485bf4b769744bd407016a2` có `correlation_id=req-5170bf64`. Root `lab-agent-run` mất 2.657 giây; child `retrieval` mất 2.503 giây trong khi `generation` chỉ 0.154 giây.
- **Root cause:** Incident `rag_slow` làm `retrieve()` sleep 2.5 giây; metrics, log và trace cùng chỉ ra retrieval là bước gây latency, không phải generation.
- **Fix action:** Đã gọi `scripts/inject_incident.py --disable` sau workload; trạng thái API xác nhận `rag_slow=false`.
- **Preventive measure:** Giữ alert `HighLatencyP95`, theo dõi retrieval span, dùng correlation ID để điều tra theo Metrics → Logs → Traces và rollback prompt nếu evidence cho thấy prompt gây regression.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Scrub PII ngay trong processor chain trước file writer/JSON renderer, đồng thời tắt capture raw input/output trong trace. Cách này bảo vệ dữ liệu ở cả log lẫn observability backend mà vẫn giữ metadata cần cho vận hành.
- **Một lỗi/blocker đã gặp:** Workload đầu tiên lấy local fallback vì prompt `day13-chat` chưa tồn tại trên Langfuse. Đã giữ fallback trung thực qua `prompt_source`/`prompt_fetch_error`, sau đó tạo v1/v2 đúng prompt contract thay vì hard-code version giả.
- **Cách tìm nguyên nhân và xử lý:** Xác định cửa sổ latency tăng trên dashboard, lọc `response_sent` để lấy `correlation_id`, mở trace cùng ID và so duration của retrieval/generation. Retrieval khoảng 2.5 giây là bước bất thường; tắt `rag_slow` để khôi phục.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics khoanh vùng triệu chứng và thời gian; logs chọn request cụ thể; traces định vị child span chậm/lỗi; chỉ kết luận root cause khi ba tín hiệu khớp.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt label giúp deploy/rollback không sửa code; token/cost phát hiện regression hiệu quả; SLO 99.5% và error budget 0.5% biến chất lượng dịch vụ thành ngưỡng có thể theo dõi và cảnh báo.
- **Điều quan trọng nhất đã học:** HTTP 200 chưa đủ để kết luận hệ thống khỏe; latency, retrieval success, token/cost và quality proxy phải được quan sát cùng nhau.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Dashboard HTML là artifact local đọc từ JSONL, không phải backend metrics production; evidence Langfuse và structured log vẫn được đối chiếu bằng correlation ID để tránh kết luận chỉ từ một nguồn.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và không lộ secret key.
- [x] Repository chạy lại được theo README.
- [x] Không có secret key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
