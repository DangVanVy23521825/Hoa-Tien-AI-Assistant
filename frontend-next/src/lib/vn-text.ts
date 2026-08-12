/**
 * Chuẩn hoá chuỗi tiếng Việt để so khớp không dấu:
 * hạ chữ thường → đổi đ/Đ thành d → bỏ dấu tổ hợp → gộp khoảng trắng.
 *
 * Thứ tự quan trọng: phải hạ chữ thường TRƯỚC để "Đ" thành "đ" rồi mới thành "d".
 * "đ" không phải chữ "d" mang dấu tổ hợp nên normalize("NFD") không tách được —
 * bắt buộc thay riêng.
 */
export function normalizeVi(input: string): string {
  return input
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
