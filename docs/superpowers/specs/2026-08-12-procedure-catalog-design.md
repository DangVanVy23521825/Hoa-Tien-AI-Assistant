# Thiết kế: nâng cấp trang "Danh mục thủ tục"

Ngày: 2026-08-12 · Trạng thái: đã duyệt

## Vấn đề

Trang `/thu-tuc` đang là **lưới phẳng 19 thẻ**, 5 lĩnh vực trộn lẫn, không có tìm kiếm.
Người dân muốn tra "đăng ký tạm trú" phải đọc mắt qua cả 19 thẻ. Trang chi tiết
`/thu-tuc/[code]` đã đầy đủ (hồ sơ, lệ phí, thời gian, nơi nộp, căn cứ pháp lý, QR,
in checklist) nhưng nút "Hỏi trợ lý về thủ tục này" **link trống sang `/tro-ly`** —
không mang câu hỏi theo, người dân sang đó vẫn phải tự gõ lại từ đầu.

Mong muốn: danh mục thủ tục trở thành một kênh tra cứu **có cấu trúc** đứng ngang hàng
với chatbot, chứ không phải danh sách phụ. Thông tin có cấu trúc + AI hội thoại, hai
lối vào cùng một kho dữ liệu.

## Tiền đề đã loại bỏ

| Ý tưởng ban đầu | Vì sao loại |
|---|---|
| Thêm mục "Quy trình 1→2→3→4" ở trang chi tiết | Không tồn tại ở bất kỳ đâu: không có cột trong bảng `procedures`, không có trong `data/seed-knowledge-base.json`. Thêm vào là **migration Alembic + tự soạn nội dung các bước cho cả 19 thủ tục** — mà không có nguồn chính thức nào để trích. Tự viết là vi phạm nguyên tắc kiến trúc #2 (không hallucinate), và đây là quy trình hành chính nên sai là sai lệch pháp lý chứ không phải lỗi UX. Tách ra làm sau, khi có nguồn từ UBND xã. |
| Nhúng ô chat thẳng vào trang chi tiết | Phải tái sử dụng toàn bộ logic chat (lịch sử, feedback 👍👎, hạn mức khách, voice, sanitize `answer_html`). Tốn công và dễ sinh lỗi hồi quy, trong khi cơ chế handoff `?q=` đã có sẵn và đã chạy tốt từ trang chủ. |
| Bố cục nhóm-theo-lĩnh-vực dạng danh sách dòng (đúng mockup gốc) | Phải bỏ lưới thẻ hiện tại đang đẹp và đúng bản sắc Hòa Tiến. Chip lọc đạt cùng mục đích (thấy được cơ cấu lĩnh vực, thu hẹp nhanh) mà giữ nguyên thiết kế. |
| Sidebar lĩnh vực cố định | Thừa với 5 lĩnh vực, và phải thiết kế riêng cho mobile. |
| Lưu trạng thái tìm/lọc vào URL (`?q=`, `?nhom=`) | Phải dùng `useSearchParams` → mất prerender tĩnh, phải bọc `Suspense`. Trang `/tro-ly` đã cố tình đọc `window.location.search` thay vì `useSearchParams` vì lý do này (`rules/frontend.md`). Không đáng cho một bộ lọc 19 mục. |

Nút thắt là **khả năng thu hẹp danh sách**, không phải thiếu dữ liệu. Nên đây là thay đổi
thuần frontend.

## Quyết định đã chốt

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Phạm vi | **Thuần frontend `frontend-next/`** | Không đụng DB, không migration, không sửa seed, không cần đồng bộ bản offline dự phòng |
| Nguồn từ khoá tìm kiếm | `keywords` từ API | `/procedures` **đã trả sẵn** `keywords` (`schemas/procedure.py` → `ProcedureBase`), chỉ thiếu ở TS type. Mỗi thủ tục có 4–6 từ dân dã: "làm giấy cho con", "sổ đỏ", "trẻ mới sinh" |
| Chuẩn hoá chữ | Bỏ dấu cả hai phía khi so khớp | Người lớn tuổi gõ không dấu. "so do" phải ra "sổ đỏ" |
| Nhiều từ khoá | Khớp **tất cả** (AND) | Gõ thêm từ là thu hẹp dần — đúng kỳ vọng |
| Danh sách lĩnh vực | **Suy ra động từ dữ liệu API** | Thêm lĩnh vực mới trong DB là chip tự hiện, không phải sửa code. Chỉ bảng emoji hardcode, thiếu thì rơi về `📋` |
| Thứ tự chip | Số lượng giảm dần | Việc dân hay làm nhất lên đầu |
| Handoff sang AI | `/tro-ly?q=…` — điền sẵn **và tự gửi** | Cơ chế đã có và đã tự động gửi khi mount (`app/tro-ly/page.tsx:167-180`), dùng lại nguyên vẹn |
| Trạng thái lọc | State cục bộ trong component | Giữ trang prerender tĩnh |

## 1. Trang danh mục `/thu-tuc`

### Thanh tìm kiếm

Lọc **tức thì khi gõ** — không cần Enter, không gọi API (19 bản ghi đã nằm sẵn trong state).

Trường được đánh chỉ mục cho mỗi thủ tục:

```
name + description + keywords[] + category + code
```

Cả chuỗi tìm và chuỗi chỉ mục đều đi qua `normalizeVi()`. Truy vấn tách theo khoảng
trắng thành các token; thủ tục khớp khi **mọi** token đều xuất hiện trong chuỗi chỉ mục.

```
"khai sinh"      → Đăng ký khai sinh
"so do"          → các thủ tục Đất đai có "sổ đỏ" trong keywords
"tam tru gia han" → thu hẹp còn đúng thủ tục gia hạn tạm trú
```

### `lib/vn-text.ts` (mới)

```ts
export function normalizeVi(s: string): string
```

Tách thành module riêng vì bỏ dấu tiếng Việt sẽ còn cần ở chỗ khác (FAQ, tìm bài viết).
Cách làm: `toLowerCase()` → `normalize("NFD")` → xoá dấu tổ hợp (`̀-ͯ`) →
thay `đ→d` → gộp khoảng trắng thừa. **`đ/Đ` phải xử lý riêng** vì nó không phải chữ `d`
có dấu tổ hợp, `NFD` không tách được.

### Hàng chip lĩnh vực

```
[Tất cả 19] [👨‍👩‍👧 Hộ tịch 6] [🏠 Cư trú 5] [🌾 Đất đai 4] [📄 Chứng thực 3] [🤝 LĐ-XH 1]
```

- Lĩnh vực và số đếm tính từ mảng procedures đã tải, không hardcode
- Chip và ô tìm kiếm **cộng dồn**: chọn "Cư trú" rồi gõ "gia han" thì lọc trong Cư trú
- Số trên chip là **tổng theo lĩnh vực**, không đổi theo ô tìm kiếm — để người dùng luôn
  thấy được cơ cấu danh mục, kể cả khi đang lọc
- Mobile: hàng chip cuộn ngang (`overflow-x-auto`), không xuống dòng vỡ bố cục

### Lưới thẻ

Giữ nguyên thiết kế thẻ hiện tại. Thêm dòng đếm phía trên lưới:

```
Hiển thị 6 / 19 thủ tục
```

Đặt `aria-live="polite"` để screen reader đọc kết quả sau mỗi lần lọc.

## 2. Trạng thái tìm không ra kết quả

Đây là phần quan trọng nhất của thiết kế, không phải trang trí.

Danh mục chỉ có **19 thủ tục**, trong khi KB có **225 bản ghi** (97 bài kiến thức về lịch
sử, văn hoá, di tích, làng nghề, các thôn + 109 FAQ). Người dân gõ "xin giấy phép xây nhà"
hay "đình làng Hòa Tiến" sẽ không ra gì và **kết luận sai rằng hệ thống không biết**.
Empty state vì vậy phải là cầu nối, không phải ngõ cụt:

```
Không tìm thấy thủ tục nào khớp "xin giấy phép xây nhà"

Trợ lý AI tra cứu rộng hơn danh mục này — kho dữ liệu của xã
có 225 bản ghi, gồm cả lịch sử, văn hoá và làng nghề.

[💬 Hỏi trợ lý: "xin giấy phép xây nhà"]   [Xoá bộ lọc]
```

Nút chính → `/tro-ly?q=<từ đã gõ>` → trợ lý trả lời ngay. Nếu câu hỏi ngoài phạm vi KB
thì guardrail hiện có (ngưỡng điểm + refusal phrase) sẽ hướng về UBND xã — vẫn không bịa.

Trường hợp lọc theo chip mà rỗng (không xảy ra với dữ liệu hiện tại nhưng có thể xảy ra
khi kết hợp chip + tìm kiếm): cùng một empty state, nút "Xoá bộ lọc" reset cả hai.

## 3. Trang chi tiết `/thu-tuc/[code]`

Đúng một thay đổi. Nút "Hỏi trợ lý về thủ tục này" hiện link trống `/tro-ly`
(`app/thu-tuc/[code]/page.tsx:172`) → đổi thành:

```
/tro-ly?q=Thủ tục ${encodeURIComponent(name)} cần chuẩn bị hồ sơ gì?
```

Câu hỏi chứa **nguyên tên thủ tục** nên nhánh keyword của `retrieve()` chắc chắn khớp,
không rơi vào fallback — không phụ thuộc vào margin hẹp của semantic.

## 4. Files thay đổi

| File | Thay đổi |
|---|---|
| `frontend-next/src/lib/api.ts` | thêm `keywords: string[]` vào interface `Procedure` |
| `frontend-next/src/lib/vn-text.ts` | **mới** — `normalizeVi()` |
| `frontend-next/src/app/thu-tuc/page.tsx` | tìm kiếm + chip lĩnh vực + lọc + empty state |
| `frontend-next/src/app/thu-tuc/[code]/page.tsx` | 1 dòng — prefill `?q=` |

Không đụng: backend, DB, `data/seed-knowledge-base.json`, `backend/data/`,
`frontend/legacy/`, `frontend-next/public/legacy/`.

## 5. Rủi ro và điểm cần biết

**Tự gửi tiêu lượt miễn phí của khách.** Khách chưa đăng nhập có `FREE_GUEST_TURNS`
lượt (mặc định 3), đếm theo `X-Guest-Id` của thiết bị. Mỗi lần bấm nút hỏi AI từ danh
mục hoặc trang chi tiết **mất 1 lượt**. Ban giám khảo bấm thử vài thủ tục là hết lượt
và bị chặn. Task này **không** đổi hạn mức — chỉ ghi nhận; nếu cần nới cho buổi thi thì
chỉnh env trên Railway, là việc vận hành riêng.

**Emoji lĩnh vực là hardcode.** Bảng ánh xạ tên lĩnh vực → emoji nằm trong code. Đổi tên
lĩnh vực trong DB (ví dụ "Lao động - Xã hội" → "Lao động, Thương binh và Xã hội") sẽ mất
emoji, rơi về `📋`. Chấp nhận được: chip vẫn hiện đúng, chỉ mất icon.

**Bỏ dấu làm tăng nhiễu.** "hoa" khớp cả "hoà", "hóa", "họa". Với 19 bản ghi thì vô hại;
nếu sau này mở tìm kiếm sang 225 bản ghi thì phải xét lại (bài học đã có ở bản offline
dự phòng: bỏ dấu xong "phở bò" trùng token với "phổ biến / bộ" — xem `rules/frontend.md`).

## 6. Kiểm thử

Không có test tự động trong repo. Kiểm bằng dev server + trình duyệt thật:

```bash
cd frontend-next && npm run dev
```

| # | Việc | Kỳ vọng |
|---|---|---|
| 1 | Mở `/thu-tuc` | 19 thẻ, 6 chip, dòng đếm "Hiển thị 19 / 19 thủ tục" |
| 2 | Gõ `khai sinh` | Còn thủ tục Đăng ký khai sinh |
| 3 | Gõ `so do` (không dấu) | Ra đúng 4 thủ tục Đất đai (DD-01…DD-04) — đều có "sổ đỏ" trong keywords |
| 4 | Bấm chip `Cư trú` | Còn 5 thẻ, dòng đếm cập nhật, số trên các chip khác **không đổi** |
| 5 | Chip `Cư trú` + gõ `dat dai` | Rỗng → hiện empty state có nút hỏi trợ lý |
| 6 | Gõ `xin giay phep xay nha` → bấm nút hỏi trợ lý | Sang `/tro-ly`, câu hỏi **tự gửi**, có câu trả lời hoặc fallback đúng |
| 7 | Bấm "Xoá bộ lọc" | Về 19 thẻ, ô tìm rỗng, chip về "Tất cả" |
| 8 | Mở một thủ tục → "Hỏi trợ lý về thủ tục này" | Sang `/tro-ly`, tự hỏi "Thủ tục … cần chuẩn bị hồ sơ gì?", trả lời khớp đúng thủ tục đó |
| 9 | Thu cửa sổ về ~375px | Hàng chip cuộn ngang, không vỡ bố cục |
| 10 | Tab bằng bàn phím | Ô tìm → từng chip → từng thẻ, focus ring rõ |
| 11 | `npm run build` | Build sạch, `/thu-tuc` vẫn prerender tĩnh |

## Ngoài phạm vi

- Mục "Quy trình các bước" (chờ nguồn chính thức từ UBND xã)
- Tìm kiếm xuyên KB 225 bản ghi ở trang danh mục (đã có trợ lý AI làm việc đó)
- Lưu bộ lọc vào URL / chia sẻ link kết quả lọc
- Đồng bộ tính năng này sang bản offline dự phòng
