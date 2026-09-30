# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `fast_successful_requests`
- Điều kiện và thời gian duy trì: P95 `response_sent.latency_ms > 3000` trong 5 phút.
- Ảnh hưởng tới người dùng: phản hồi chậm, có thể vượt SLO.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency, xác nhận P95/P99 và time range.
  2. Lọc `response_sent` có latency cao, lấy `correlation_id`.
  3. Mở trace cùng ID, so sánh retrieval và generation.
- Mitigation tạm thời: rollback prompt candidate, tắt incident practice hoặc giảm tải.
- Owner: `DaoMinhHieu-2A202602561`

## Alert 2

- Tên: `ElevatedErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: error budget và `fast_successful_requests`
- Điều kiện và thời gian duy trì: error rate > 2% trong 5 phút.
- Ảnh hưởng tới người dùng: request thất bại hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, xác nhận error rate và error type.
  2. Lọc `request_failed` theo thời gian, lấy `correlation_id`.
  3. Mở trace cùng ID, kiểm tra span retrieval/generation và lỗi.
- Mitigation tạm thời: tắt scenario gây lỗi, khôi phục cấu hình trước đó và retry workload nhỏ.
- Owner: `DaoMinhHieu-2A202602561`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success guardrail >= 90%.
- Điều kiện và thời gian duy trì: retrieval success < 90% trong 10 phút, tính trên mọi event có `tool_success`.
- Ảnh hưởng tới người dùng: câu trả lời thiếu context hoặc kém tin cậy.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, kiểm tra retrieval success theo time range.
  2. Lọc event có `tool_success=false`, lấy `correlation_id`.
  3. Mở trace cùng ID, kiểm tra retrieval span và generation metadata.
- Mitigation tạm thời: chuyển về prompt production đã biết ổn định, tắt incident retrieval và kiểm tra backend dữ liệu.
- Owner: `DaoMinhHieu-2A202602561`
