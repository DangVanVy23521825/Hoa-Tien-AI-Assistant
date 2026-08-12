import type { Procedure } from "./api.ts";
import { normalizeVi } from "./vn-text.ts";

/**
 * Emoji cho từng lĩnh vực. Danh sách lĩnh vực KHÔNG hardcode ở đây — nó được suy ra
 * từ dữ liệu API. Bảng này chỉ để gắn icon; lĩnh vực mới trong DB vẫn hiện chip,
 * chỉ là dùng icon mặc định.
 */
export const CATEGORY_ICONS: Record<string, string> = {
  "Hộ tịch": "👨‍👩‍👧",
  "Cư trú": "🏠",
  "Đất đai": "🌾",
  "Chứng thực": "📄",
  "Lao động - Xã hội": "🤝",
};

export const DEFAULT_CATEGORY_ICON = "📋";

export function categoryIcon(category: string): string {
  return CATEGORY_ICONS[category] ?? DEFAULT_CATEGORY_ICON;
}

export interface CategoryFacet {
  category: string;
  count: number;
  icon: string;
}

/**
 * Số đếm là TỔNG theo lĩnh vực trên toàn danh mục — cố ý không phụ thuộc ô tìm kiếm,
 * để người dùng luôn thấy được cơ cấu danh mục kể cả khi đang lọc.
 */
export function categoryFacets(procedures: Procedure[]): CategoryFacet[] {
  const counts = new Map<string, number>();
  for (const p of procedures) {
    counts.set(p.category, (counts.get(p.category) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([category, count]) => ({ category, count, icon: categoryIcon(category) }))
    .sort((a, b) => b.count - a.count || a.category.localeCompare(b.category, "vi"));
}

/**
 * Chuỗi được đánh chỉ mục cho một thủ tục, đã chuẩn hoá không dấu.
 *
 * CỐ Ý KHÔNG có `description`. Đo trên dữ liệu thật: đưa description vào thì "khai sinh"
 * ra 3 kết quả — lẫn cả "Đăng ký tạm trú" (`sinh` khớp "sinh sống", `khai` khớp
 * "khai báo") — và "so do" ra 5, lẫn "cải chính hộ tịch" (`so` khớp "sổ hộ tịch",
 * `do` khớp "thay đổi"). Bỏ description thì còn lần lượt 2 và 4, đều đúng.
 * Cùng nguyên tắc với bản offline dự phòng: chỉ mục tiêu đề + từ khoá, không toàn văn.
 */
export function searchIndex(p: Procedure): string {
  return normalizeVi([p.name, p.category, p.code, ...(p.keywords ?? [])].join(" "));
}

export interface FilterOptions {
  query: string;
  category: string | null;
}

/** Lọc theo chip lĩnh vực và ô tìm kiếm; nhiều token trong truy vấn là AND. */
export function filterProcedures(
  procedures: Procedure[],
  { query, category }: FilterOptions,
): Procedure[] {
  const tokens = normalizeVi(query).split(" ").filter(Boolean);
  return procedures.filter((p) => {
    if (category !== null && p.category !== category) return false;
    if (tokens.length === 0) return true;
    const haystack = searchIndex(p);
    return tokens.every((token) => haystack.includes(token));
  });
}
