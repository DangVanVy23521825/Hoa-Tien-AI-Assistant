# Thiết kế: trang thông tin tài khoản

Ngày: 2026-08-13 · Trạng thái: đã duyệt

## Vấn đề

**Nguyên nhân thật, tìm ra khi kiểm trên trình duyệt:** bấm nút tài khoản làm **sập cả
trang**, không phải chỉ "không có chỗ để đi". `DropdownMenuLabel` (khối tên + email) là
`Menu.GroupLabel` của base-ui, bắt buộc phải nằm trong `Menu.Group`; nó đang nằm trực
tiếp trong `DropdownMenuContent` nên base-ui ném `MenuGroupContext is missing`, React gỡ
cả cây React và người dùng thấy trang trắng "This page couldn't load" — dễ nhầm là lỗi
404 của Vercel. Lỗi này có sẵn từ trước, không liên quan tới trang tài khoản.

Ngoài ra, kể cả khi dropdown mở được thì nó cũng **không đi được đâu cả**.
Dropdown hiện có đúng ba thứ: nhãn tên + email (không bấm được), "Thống kê" (chỉ hiện
với admin, mở modal chứ không chuyển trang), và "Đăng xuất". Không có `href` nào, và
trong toàn bộ `frontend-next/src` không có tham chiếu tới một route tài khoản nào.

Hệ quả: tài khoản là thứ người dân bỏ công xác thực email qua OTP mới có, nhưng sau đó
không có chỗ nào để xem lại nó — không biết mình đăng nhập bằng email nào, đã hỏi bao
nhiêu câu, đã gửi bao nhiêu phản ánh.

## Tiền đề đã loại bỏ

| Ý tưởng | Vì sao loại |
|---|---|
| Hiện ngày tạo tài khoản | `/auth/login` trả `User` chỉ gồm `id`, `email`, `display_name`, `role` — không có `created_at`. Thêm phải sửa schema backend, mà người đang đăng nhập sẵn vẫn thấy thiếu vì object user được cache trong `localStorage` từ lúc đăng nhập. Không đáng cho một dòng ngày tháng. |
| Sửa tên / đổi mật khẩu | Cần thêm endpoint `PATCH /auth/me` và luồng đổi mật khẩu ở backend; đổi mật khẩu còn kéo theo chuyện xác thực lại. Ngoài phạm vi lần này. |
| Nhúng luôn danh sách lịch sử chat và phản ánh vào trang | Trùng lặp với `/tro-ly` (đã có lịch sử) và `/phan-anh` (đã có "Phản ánh của tôi"). Chỉ hiện **số đếm** rồi liên kết sang đó. |

## Quyết định đã chốt

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Phạm vi | **Thuần frontend** | Mọi dữ liệu cần đã có sẵn từ `useAuth()`, `/chat/history`, `/reports/me` |
| Route | `/tai-khoan` | Đồng bộ với nếp đặt tên tiếng Việt không dấu của các route khác |
| Chưa đăng nhập | Hiện lời mời đăng nhập, **không** render phần còn lại | Giống `/phan-anh`; không hiện thông tin rỗng rồi mới báo lỗi |
| Hai số đếm | Gọi độc lập, hỏng cái nào thì cái đó hiện `—` | Thông tin tài khoản lấy từ `useAuth()` nên không phụ thuộc mạng — backend sập vẫn xem được mình là ai |

## 1. Sửa gốc

### 1a. Bọc `DropdownMenuLabel` trong `DropdownMenuGroup`

Đây mới là thứ làm sập trang. `DropdownMenuGroup` đã có sẵn trong
`components/ui/dropdown-menu.tsx`, chỉ chưa được dùng.

### 1b. Thêm lối vào

- **Dropdown desktop** (`components/header.tsx`): thêm mục **"Tài khoản"** trỏ `/tai-khoan`,
  đặt trên "Thống kê" và "Đăng xuất".
- **Menu mobile**: khi đã đăng nhập, thêm liên kết "Tài khoản" vào cuối danh sách nav.
  Hiện menu mobile không có lối nào tới khu vực tài khoản.

## 2. Trang `/tai-khoan`

Client component, metadata đặt trong `layout.tsx` cùng thư mục theo đúng quy ước hiện có.

- **Thẻ thông tin**: chữ cái đầu của `display_name` làm avatar, họ tên, email, huy hiệu
  vai trò — `admin` hiển thị "Quản trị viên", còn lại "Người dân".
- **Hai ô số liệu**:
  - "N câu đã hỏi" — đếm độ dài mảng `/chat/history`, liên kết `/tro-ly`
  - "M phản ánh đã gửi" — đếm độ dài mảng `/reports/me`, liên kết `/phan-anh`
- **Nút đăng xuất** — gọi `logout()` của `useAuth()` rồi chuyển về trang chủ.

## 3. Xử lý lỗi

Hai lời gọi đếm số chạy độc lập (`Promise` riêng, không `Promise.all`): một cái hỏng
không kéo cái kia xuống. Trạng thái mỗi ô là `number | null`; `null` hiển thị `—`.

Thông tin tài khoản **không** phụ thuộc API — lấy từ `localStorage` qua `useAuth()`.

## 4. Files

| File | Thay đổi |
|---|---|
| `frontend-next/src/app/tai-khoan/page.tsx` | **mới** |
| `frontend-next/src/app/tai-khoan/layout.tsx` | **mới** — metadata |
| `frontend-next/src/components/header.tsx` | thêm lối vào ở dropdown desktop và menu mobile |

Không đụng backend, DB, seed, bản offline dự phòng.

## 5. Kiểm thử

| # | Việc | Kỳ vọng |
|---|---|---|
| 1 | Mở `/tai-khoan` khi chưa đăng nhập | Lời mời đăng nhập, không hiện thông tin |
| 2 | Đăng nhập rồi mở lại | Đúng họ tên, email, huy hiệu "Người dân" |
| 3 | Hai ô số liệu | Khớp số thật trong `/chat/history` và `/reports/me` |
| 4 | Bấm ô số liệu | Sang đúng `/tro-ly` và `/phan-anh` |
| 5 | Tắt backend rồi tải lại | Vẫn hiện tên/email; hai ô ra `—`; trang không vỡ |
| 6 | Bấm nút tài khoản trên header | Dropdown mở ra, **trang không sập** |
| 6b | Dropdown → "Tài khoản" | Render thành `<a href="/tai-khoan">` thật và tới đúng nơi |
| 7 | Menu mobile khi đã đăng nhập | Có mục "Tài khoản", bấm tới nơi |
| 8 | Bấm "Đăng xuất" | Về trang chủ, header trở lại nút "Đăng nhập" |
| 9 | `npm run lint && npm run build` | Sạch, `/tai-khoan` prerender tĩnh |

## Ngoài phạm vi

Sửa tên hiển thị · đổi mật khẩu · xoá tài khoản · ngày tạo tài khoản · trang quản trị
cho admin.
