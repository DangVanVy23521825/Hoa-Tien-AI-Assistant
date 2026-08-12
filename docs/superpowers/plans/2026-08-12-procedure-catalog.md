# Nâng cấp trang "Danh mục thủ tục" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trang `/thu-tuc` có tìm kiếm bỏ dấu + chip lọc lĩnh vực + trạng thái rỗng dẫn sang trợ lý AI; nút "Hỏi trợ lý về thủ tục này" mang câu hỏi theo thay vì link trống.

**Architecture:** Toàn bộ logic lọc/chuẩn hoá chữ nằm trong hai module thuần (`lib/vn-text.ts`, `lib/procedure-filter.ts`) không phụ thuộc React — test được bằng `node --test`. Component React chỉ giữ state và render. Dữ liệu vẫn lấy một lần từ `GET /procedures` như hiện tại, lọc hoàn toàn ở client (19 bản ghi), không thêm request nào.

**Tech Stack:** Next.js 16 App Router (client components), TypeScript, Tailwind v4, shadcn/base-ui, `node --test` + `--experimental-strip-types` (có sẵn trong Node 22.14, **không thêm dependency nào**).

**Spec:** `docs/superpowers/specs/2026-08-12-procedure-catalog-design.md`

## Global Constraints

- **Không thêm dependency** vào `frontend-next/package.json`. Test chạy bằng test runner built-in của Node.
- **Không đụng**: backend, DB, migration, `data/seed-knowledge-base.json`, `backend/data/`, `frontend/` (vanilla), `frontend/legacy/`, `frontend-next/public/legacy/`.
- **Không dùng `useSearchParams`** trong `app/thu-tuc/**` — trang phải giữ prerender tĩnh (`rules/frontend.md`). Trạng thái tìm/lọc chỉ nằm trong state cục bộ, không sync vào URL.
- **Số trên chip lĩnh vực là tổng theo lĩnh vực**, KHÔNG đổi khi gõ ô tìm kiếm.
- **Khớp tìm kiếm là AND**: mọi token trong truy vấn đều phải xuất hiện.
- Lĩnh vực **suy ra động từ dữ liệu API**, không hardcode danh sách. Chỉ bảng emoji hardcode, thiếu thì rơi về `📋`.
- Mọi chữ hiển thị bằng **tiếng Việt có dấu**.
- Giữ nguyên thiết kế thẻ thủ tục hiện có (màu `paddy` / `river` / `line` / `ink-soft`, bo góc, hover nhấc thẻ).
- Mọi lệnh chạy từ thư mục `frontend-next/`.

---

### Task 1: Hạ tầng test + chuẩn hoá chữ tiếng Việt

**Files:**
- Modify: `frontend-next/tsconfig.json`
- Modify: `frontend-next/package.json`
- Create: `frontend-next/src/lib/vn-text.ts`
- Test: `frontend-next/src/lib/vn-text.test.ts`

**Interfaces:**
- Consumes: (không có — task đầu tiên)
- Produces: `normalizeVi(input: string): string` — hạ chữ thường, đổi `đ/Đ → d`, bỏ toàn bộ dấu tổ hợp, gộp khoảng trắng thừa, trim.

**Bối cảnh cần biết:** Repo chưa có test runner nào. Node 22.14 chạy được file `.ts` bằng `--experimental-strip-types`, nhưng **bắt buộc import kèm đuôi `.ts`** (import không đuôi sẽ `ERR_MODULE_NOT_FOUND`). Vì vậy tsconfig phải bật `allowImportingTsExtensions` (hợp lệ vì `noEmit: true` đã bật sẵn). Cả hai điều này đã được kiểm chứng thực tế trước khi viết plan.

- [ ] **Step 1: Bật `allowImportingTsExtensions` trong tsconfig**

Trong `frontend-next/tsconfig.json`, thêm đúng một dòng vào `compilerOptions`, ngay dưới `"noEmit": true`:

```json
    "noEmit": true,
    "allowImportingTsExtensions": true,
```

- [ ] **Step 2: Thêm script test vào package.json**

Trong `frontend-next/package.json`, thêm vào `"scripts"` (sau `"lint"`):

```json
    "lint": "eslint",
    "test": "node --experimental-strip-types --test \"src/**/*.test.ts\""
```

Dấu nháy quanh glob là **bắt buộc** — để Node tự khai triển glob thay vì shell.

- [ ] **Step 3: Viết test thất bại cho `normalizeVi`**

Tạo `frontend-next/src/lib/vn-text.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizeVi } from "./vn-text.ts";

test("hạ chữ thường và bỏ dấu thanh", () => {
  assert.equal(normalizeVi("Đăng ký khai sinh"), "dang ky khai sinh");
});

test("đổi đ/Đ thành d — NFD không tách được chữ này", () => {
  assert.equal(normalizeVi("Sổ đỏ"), "so do");
  assert.equal(normalizeVi("ĐẤT ĐAI"), "dat dai");
});

test("gộp khoảng trắng thừa và trim", () => {
  assert.equal(normalizeVi("  Tạm   trú  "), "tam tru");
});

test("chuỗi đã không dấu thì giữ nguyên", () => {
  assert.equal(normalizeVi("khai sinh"), "khai sinh");
});

test("chuỗi rỗng trả về chuỗi rỗng", () => {
  assert.equal(normalizeVi(""), "");
  assert.equal(normalizeVi("   "), "");
});

test("giữ nguyên chữ số và dấu gạch trong mã thủ tục", () => {
  assert.equal(normalizeVi("DD-01"), "dd-01");
});
```

- [ ] **Step 4: Chạy test để xác nhận nó thất bại**

Run: `cd frontend-next && npm test`
Expected: FAIL — `Cannot find module '.../src/lib/vn-text.ts'`

- [ ] **Step 5: Viết `normalizeVi`**

Tạo `frontend-next/src/lib/vn-text.ts`:

```ts
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
```

- [ ] **Step 6: Chạy test để xác nhận nó pass**

Run: `cd frontend-next && npm test`
Expected: PASS — `# pass 6`, `# fail 0`

- [ ] **Step 7: Xác nhận build và lint không vỡ vì tsconfig/test file**

Run: `cd frontend-next && npm run lint && npm run build`
Expected: cả hai sạch. `npm run build` phải in ra route `/thu-tuc` với dấu prerender tĩnh (`○`).

Nếu `npm run build` báo lỗi typecheck ở file `.test.ts`: fallback là chuyển các file test sang `frontend-next/tests/` và thêm `"tests"` vào mảng `exclude` của tsconfig, đồng thời sửa glob trong script test thành `"tests/**/*.test.ts"` và sửa đường dẫn import trong test thành `../src/lib/vn-text.ts`.

- [ ] **Step 8: Commit**

```bash
git add frontend-next/tsconfig.json frontend-next/package.json frontend-next/src/lib/vn-text.ts frontend-next/src/lib/vn-text.test.ts
git commit -m "feat(fe): normalizeVi bỏ dấu tiếng Việt + hạ tầng test node --test

Test chạy bằng test runner built-in của Node 22, không thêm dependency."
```

---

### Task 2: Logic lọc thủ tục và thống kê lĩnh vực

**Files:**
- Modify: `frontend-next/src/lib/api.ts` (interface `Procedure`, khoảng dòng 21–33)
- Create: `frontend-next/src/lib/procedure-filter.ts`
- Test: `frontend-next/src/lib/procedure-filter.test.ts`

**Interfaces:**
- Consumes: `normalizeVi(input: string): string` từ `./vn-text.ts` (Task 1)
- Produces:
  - `CATEGORY_ICONS: Record<string, string>`
  - `DEFAULT_CATEGORY_ICON: string` (`"📋"`)
  - `categoryIcon(category: string): string`
  - `interface CategoryFacet { category: string; count: number; icon: string }`
  - `categoryFacets(procedures: Procedure[]): CategoryFacet[]`
  - `searchIndex(p: Procedure): string`
  - `interface FilterOptions { query: string; category: string | null }`
  - `filterProcedures(procedures: Procedure[], options: FilterOptions): Procedure[]`

**Bối cảnh cần biết:** `GET /procedures` **đã trả sẵn `keywords`** (xác nhận trong `backend/app/schemas/procedure.py` → `ProcedureBase`), chỉ interface TS ở frontend là thiếu. Không cần sửa backend.

Trong `procedure-filter.ts`, `Procedure` phải import bằng **`import type`** (không phải `import`). Lý do: type-only import bị xoá hoàn toàn khi Node strip types, nên Node không phải resolve alias `@/` mà nó không hiểu. Import giá trị (`normalizeVi`) thì bắt buộc dùng đường dẫn tương đối kèm đuôi `.ts`.

- [ ] **Step 1: Thêm `keywords` vào interface `Procedure`**

Trong `frontend-next/src/lib/api.ts`, thêm một dòng vào interface `Procedure`, ngay sau `category`:

```ts
export interface Procedure {
  id: string;
  code: string;
  name: string;
  category: string;
  keywords: string[];
  description: string;
  documents: string[];
  fee: string;
  processing_time: string;
  place_of_submission: string;
  legal_basis: string;
  online_url: string;
}
```

- [ ] **Step 2: Viết test thất bại cho logic lọc**

Tạo `frontend-next/src/lib/procedure-filter.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import type { Procedure } from "./api.ts";
import {
  categoryFacets,
  categoryIcon,
  filterProcedures,
} from "./procedure-filter.ts";

function proc(over: Partial<Procedure>): Procedure {
  return {
    id: "00000000-0000-0000-0000-000000000000",
    code: "XX-00",
    name: "Thủ tục mẫu",
    category: "Hộ tịch",
    keywords: [],
    description: "Mô tả mẫu",
    documents: [],
    fee: "Miễn phí",
    processing_time: "Trong ngày",
    place_of_submission: "Trung tâm Phục vụ hành chính công cấp xã Hòa Tiến",
    legal_basis: "Luật Hộ tịch 2014",
    online_url: "https://dichvucong.gov.vn",
    ...over,
  };
}

const FIXTURE: Procedure[] = [
  proc({ code: "KS-01", name: "Đăng ký khai sinh", category: "Hộ tịch",
         keywords: ["khai sinh", "làm giấy cho con"] }),
  proc({ code: "KT-01", name: "Đăng ký kết hôn", category: "Hộ tịch",
         keywords: ["kết hôn", "đăng ký kết hôn"] }),
  proc({ code: "CU-02", name: "Đăng ký tạm trú", category: "Cư trú",
         keywords: ["tạm trú", "gia hạn tạm trú"] }),
  proc({ code: "DD-02", name: "Cấp đổi, cấp lại Giấy chứng nhận quyền sử dụng đất",
         category: "Đất đai", keywords: ["cấp lại sổ đỏ", "sổ đỏ bị mất"] }),
];

const NO_FILTER = { query: "", category: null };

test("không lọc gì thì trả về toàn bộ danh sách", () => {
  assert.equal(filterProcedures(FIXTURE, NO_FILTER).length, 4);
});

test("khoảng trắng thuần không tính là truy vấn", () => {
  assert.equal(filterProcedures(FIXTURE, { query: "   ", category: null }).length, 4);
});

test("khớp theo tên, gõ không dấu", () => {
  const got = filterProcedures(FIXTURE, { query: "khai sinh", category: null });
  assert.deepEqual(got.map((p) => p.code), ["KS-01"]);
});

test("khớp theo keywords, gõ không dấu — 'so do' ra thủ tục đất đai", () => {
  const got = filterProcedures(FIXTURE, { query: "so do", category: null });
  assert.deepEqual(got.map((p) => p.code), ["DD-02"]);
});

test("khớp theo mã thủ tục", () => {
  const got = filterProcedures(FIXTURE, { query: "cu-02", category: null });
  assert.deepEqual(got.map((p) => p.code), ["CU-02"]);
});

test("khớp theo tên lĩnh vực", () => {
  const got = filterProcedures(FIXTURE, { query: "dat dai", category: null });
  assert.deepEqual(got.map((p) => p.code), ["DD-02"]);
});

test("KHÔNG đánh chỉ mục description — nguồn nhiễu chính", () => {
  const noisy = proc({
    code: "NOISE-01",
    name: "Thủ tục không liên quan",
    category: "Chứng thực",
    keywords: [],
    description: "Áp dụng cho công dân sinh sống tại xã, cần khai báo trước.",
  });
  const got = filterProcedures([...FIXTURE, noisy], {
    query: "khai sinh",
    category: null,
  });
  assert.deepEqual(got.map((p) => p.code), ["KS-01"]);
});

test("nhiều token là AND — phải khớp tất cả", () => {
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "gia han tam tru", category: null })
      .map((p) => p.code),
    ["CU-02"],
  );
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "khai sinh ket hon", category: null }),
    [],
  );
});

test("chip lĩnh vực lọc độc lập", () => {
  const got = filterProcedures(FIXTURE, { query: "", category: "Hộ tịch" });
  assert.deepEqual(got.map((p) => p.code), ["KS-01", "KT-01"]);
});

test("chip và ô tìm kiếm cộng dồn", () => {
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "dang ky", category: "Cư trú" })
      .map((p) => p.code),
    ["CU-02"],
  );
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "dat dai", category: "Cư trú" }),
    [],
  );
});

test("categoryFacets đếm đúng và sắp theo số lượng giảm dần", () => {
  const facets = categoryFacets(FIXTURE);
  assert.deepEqual(
    facets.map((f) => [f.category, f.count]),
    [["Hộ tịch", 2], ["Cư trú", 1], ["Đất đai", 1]],
  );
});

test("categoryFacets gắn emoji, lĩnh vực lạ rơi về 📋", () => {
  const facets = categoryFacets([...FIXTURE, proc({ code: "ZZ-01", category: "Lĩnh vực mới" })]);
  const found = facets.find((f) => f.category === "Lĩnh vực mới");
  assert.equal(found?.icon, "📋");
  assert.equal(categoryIcon("Hộ tịch"), "👨‍👩‍👧");
});

test("danh sách rỗng không làm vỡ facets", () => {
  assert.deepEqual(categoryFacets([]), []);
});
```

- [ ] **Step 3: Chạy test để xác nhận nó thất bại**

Run: `cd frontend-next && npm test`
Expected: FAIL — `Cannot find module '.../src/lib/procedure-filter.ts'`. Các test của `vn-text` vẫn pass.

- [ ] **Step 4: Viết `procedure-filter.ts`**

Tạo `frontend-next/src/lib/procedure-filter.ts`:

```ts
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
  return normalizeVi(
    [p.name, p.category, p.code, ...(p.keywords ?? [])].join(" "),
  );
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
```

- [ ] **Step 5: Chạy test để xác nhận nó pass**

Run: `cd frontend-next && npm test`
Expected: PASS — `# fail 0`, tổng 19 test (6 của vn-text + 13 của procedure-filter).

- [ ] **Step 6: Kiểm lint + build**

Run: `cd frontend-next && npm run lint && npm run build`
Expected: sạch.

- [ ] **Step 7: Commit**

```bash
git add frontend-next/src/lib/api.ts frontend-next/src/lib/procedure-filter.ts frontend-next/src/lib/procedure-filter.test.ts
git commit -m "feat(fe): logic lọc thủ tục theo từ khoá không dấu và lĩnh vực

API đã trả sẵn keywords, chỉ bổ sung vào interface TS."
```

---

### Task 3: Giao diện trang danh mục `/thu-tuc`

**Files:**
- Modify: `frontend-next/src/app/thu-tuc/page.tsx` (viết lại toàn bộ)

**Interfaces:**
- Consumes: `filterProcedures`, `categoryFacets`, `FilterOptions`, `CategoryFacet` từ `@/lib/procedure-filter` (Task 2); `api.getProcedures()` và type `Procedure` từ `@/lib/api`
- Produces: (không có — task này là lá)

**Bối cảnh cần biết:**
- Trong file **component React** thì import theo alias `@/lib/...` như phần còn lại của codebase (quy ước không đuôi `.ts`). Chỉ file test và module được test mới dùng đường dẫn tương đối kèm đuôi.
- Component `Input` có sẵn ở `@/components/ui/input`, `Button` ở `@/components/ui/button`.
- Giữ nguyên phần `<Badge>` "Dịch vụ công", tiêu đề và thẻ thủ tục của bản hiện tại.

- [ ] **Step 1: Viết lại `page.tsx`**

Thay toàn bộ nội dung `frontend-next/src/app/thu-tuc/page.tsx` bằng:

```tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { api, Procedure } from "@/lib/api";
import { categoryFacets, filterProcedures } from "@/lib/procedure-filter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Clock,
  DollarSign,
  ArrowRight,
  Search,
  MessageSquare,
  X,
} from "lucide-react";

export default function ThuTucPage() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProcedures()
      .then(setProcedures)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const facets = useMemo(() => categoryFacets(procedures), [procedures]);
  const visible = useMemo(
    () => filterProcedures(procedures, { query, category }),
    [procedures, query, category],
  );

  const trimmed = query.trim();
  const isFiltering = trimmed !== "" || category !== null;
  const clearFilters = () => {
    setQuery("");
    setCategory(null);
  };

  const chipBase =
    "shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors cursor-pointer";
  const chipOn = "bg-paddy text-white border-paddy";
  const chipOff = "bg-white text-ink-soft border-line hover:border-paddy hover:text-paddy-deep";

  return (
    <section className="max-w-6xl mx-auto px-6 py-14">
      <div className="mb-6">
        <Badge
          variant="secondary"
          className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
          Dịch vụ công
        </Badge>
        <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
          Danh mục thủ tục hành chính
        </h2>
        <p className="mt-2 text-ink-soft max-w-xl">
          Nhấn vào từng thủ tục để xem hồ sơ cần chuẩn bị, lệ phí, thời gian xử
          lý và mã QR nộp trực tuyến.
        </p>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-soft pointer-events-none" />
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Tìm thủ tục"
          placeholder="Tìm thủ tục: khai sinh, tạm trú, sổ đỏ…"
          className="h-11 pl-10 pr-4 rounded-xl border-line bg-white text-[15px]"
        />
      </div>

      <div
        className="flex gap-2 overflow-x-auto pb-2 mb-4 -mx-1 px-1"
        role="group"
        aria-label="Lọc theo lĩnh vực"
      >
        <button
          type="button"
          onClick={() => setCategory(null)}
          aria-pressed={category === null}
          className={`${chipBase} ${category === null ? chipOn : chipOff}`}
        >
          Tất cả
          <span className="opacity-70">{procedures.length}</span>
        </button>
        {facets.map((f) => (
          <button
            key={f.category}
            type="button"
            onClick={() => setCategory(f.category)}
            aria-pressed={category === f.category}
            className={`${chipBase} ${category === f.category ? chipOn : chipOff}`}
          >
            <span aria-hidden="true">{f.icon}</span>
            {f.category}
            <span className="opacity-70">{f.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-ink-soft">Đang tải...</div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-4 text-sm text-ink-soft">
            <span aria-live="polite">
              Hiển thị {visible.length} / {procedures.length} thủ tục
            </span>
            {isFiltering && (
              <button
                type="button"
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-paddy-deep font-medium hover:underline cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
                Xoá bộ lọc
              </button>
            )}
          </div>

          {visible.length === 0 ? (
            <div className="border border-line rounded-2xl bg-cream px-6 py-10 text-center">
              <p className="font-semibold mb-2">
                {trimmed
                  ? `Không tìm thấy thủ tục nào khớp “${trimmed}”`
                  : "Không có thủ tục nào trong lĩnh vực này"}
              </p>
              <p className="text-sm text-ink-soft max-w-md mx-auto mb-6">
                Trợ lý AI tra cứu rộng hơn danh mục này — kho dữ liệu của xã có
                225 bản ghi, gồm cả lịch sử, văn hoá và làng nghề.
              </p>
              <div className="flex flex-wrap gap-3 justify-center">
                {trimmed && (
                  <Link href={`/tro-ly?q=${encodeURIComponent(trimmed)}`}>
                    <Button className="bg-paddy hover:bg-paddy-deep gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Hỏi trợ lý: “{trimmed}”
                    </Button>
                  </Link>
                )}
                <Button
                  variant="outline"
                  onClick={clearFilters}
                  className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
                >
                  <X className="w-4 h-4" />
                  Xoá bộ lọc
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {visible.map((p) => (
                <Link key={p.code} href={`/thu-tuc/${p.code}`}>
                  <Card className="group relative cursor-pointer hover:shadow-lg hover:-translate-y-1 hover:border-[#d3ead9] transition-all h-full">
                    <CardHeader className="pb-3">
                      <div className="text-[11px] font-semibold tracking-wider uppercase text-river mb-2">
                        {p.category}
                      </div>
                      <CardTitle className="text-lg">{p.name}</CardTitle>
                      <CardDescription className="text-ink-soft">
                        {p.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-3.5 text-xs text-ink-soft">
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-3.5 h-3.5 text-paddy-deep" />
                          <span className="font-semibold text-paddy-deep">
                            Phí:
                          </span>{" "}
                          {p.fee.split("(")[0]}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-paddy-deep" />
                          {p.processing_time}
                        </span>
                      </div>
                    </CardContent>
                    <div className="absolute top-5 right-5 text-line group-hover:text-paddy transition-colors">
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Kiểm lint và build**

Run: `cd frontend-next && npm run lint && npm run build`
Expected: sạch; route `/thu-tuc` vẫn được đánh dấu prerender tĩnh.

- [ ] **Step 3: Kiểm bằng trình duyệt thật**

Run: `cd frontend-next && npm run dev` rồi mở `http://localhost:3000/thu-tuc`

Đối chiếu từng dòng (dừng lại và báo nếu có dòng nào sai):

Các con số dưới đây đã được **đo trước bằng chính thuật toán này trên `data/seed-knowledge-base.json`**, không phải ước lượng. Lệch số nghĩa là có lỗi thật — dừng lại và báo.

| # | Việc | Kỳ vọng |
|---|---|---|
| 1 | Mở trang | 19 thẻ; 6 chip (Tất cả 19 · Hộ tịch 6 · Cư trú 5 · Đất đai 4 · Chứng thực 3 · LĐ-XH 1); "Hiển thị 19 / 19 thủ tục" |
| 2 | Gõ `khai sinh` | **2 kết quả**: KS-01 Đăng ký khai sinh + HT-04 (từ khoá "sửa giấy khai sinh") |
| 3 | Gõ `so do` (không dấu) | **4 kết quả**: đúng DD-01…DD-04 |
| 4 | Gõ `tam tru` | **2 kết quả**: CU-02 Đăng ký tạm trú + CU-04 Khai báo tạm vắng (khớp qua lĩnh vực "Cư trú" — đã biết và chấp nhận) |
| 5 | Gõ `thuong tru` | **1 kết quả**: CU-01 |
| 6 | Bấm chip `Cư trú` | Còn 5 thẻ; dòng đếm cập nhật; **số trên các chip khác không đổi** |
| 7 | Chip `Cư trú` + gõ `dat dai` | Rỗng → hiện empty state có nút "Hỏi trợ lý" |
| 8 | Gõ `xin giay phep xay nha` rồi bấm "Hỏi trợ lý" | Sang `/tro-ly`, câu hỏi **tự gửi**, có trả lời hoặc fallback đúng |
| 9 | Bấm "Xoá bộ lọc" | Về 19 thẻ, ô tìm rỗng, chip về "Tất cả" |
| 10 | Thu cửa sổ về ~375px | Hàng chip cuộn ngang, không vỡ bố cục |
| 11 | Tab bằng bàn phím | Ô tìm → từng chip → từng thẻ; focus ring rõ |

Lưu ý ca 8: cần backend chạy được (mặc định `lib/api.ts` trỏ domain Railway production). Nếu backend không với tới được thì ghi nhận là chưa kiểm được ca này thay vì bỏ qua im lặng.

- [ ] **Step 4: Commit**

```bash
git add frontend-next/src/app/thu-tuc/page.tsx
git commit -m "feat(fe): tìm kiếm không dấu + chip lọc lĩnh vực cho danh mục thủ tục

Tìm không ra kết quả thì dẫn thẳng sang trợ lý AI với câu hỏi điền sẵn,
vì danh mục chỉ có 19 thủ tục còn KB có 225 bản ghi."
```

---

### Task 4: Nút "Hỏi trợ lý về thủ tục này" mang câu hỏi theo

**Files:**
- Modify: `frontend-next/src/app/thu-tuc/[code]/page.tsx` (khối `<Link href="/tro-ly">` ở cuối file)

**Interfaces:**
- Consumes: cơ chế handoff `?q=` có sẵn ở `app/tro-ly/page.tsx:167-180` — đọc `window.location.search`, xoá query khỏi URL bằng `replaceState`, rồi gọi `ask(q)` ngay khi mount
- Produces: (không có — task cuối)

- [ ] **Step 1: Sửa link để mang câu hỏi theo**

Trong `frontend-next/src/app/thu-tuc/[code]/page.tsx`, tìm khối:

```tsx
        <Link href="/tro-ly">
          <Button className="bg-paddy hover:bg-paddy-deep gap-2">
            <MessageSquare className="w-4 h-4" />
            Hỏi trợ lý về thủ tục này
          </Button>
        </Link>
```

Thay bằng:

```tsx
        <Link
          href={`/tro-ly?q=${encodeURIComponent(
            `Thủ tục ${procedure.name} cần chuẩn bị hồ sơ gì?`,
          )}`}
        >
          <Button className="bg-paddy hover:bg-paddy-deep gap-2">
            <MessageSquare className="w-4 h-4" />
            Hỏi trợ lý về thủ tục này
          </Button>
        </Link>
```

Câu hỏi chứa nguyên tên thủ tục nên nhánh keyword của `retrieve()` chắc chắn khớp, không phụ thuộc vào margin hẹp của semantic.

- [ ] **Step 2: Kiểm lint và build**

Run: `cd frontend-next && npm run lint && npm run build`
Expected: sạch.

- [ ] **Step 3: Kiểm bằng trình duyệt thật**

Run: `cd frontend-next && npm run dev`

| # | Việc | Kỳ vọng |
|---|---|---|
| 1 | Mở `/thu-tuc/KS-01` → bấm "Hỏi trợ lý về thủ tục này" | Sang `/tro-ly`, tự gửi "Thủ tục Đăng ký khai sinh cần chuẩn bị hồ sơ gì?", trả lời khớp đúng thủ tục khai sinh |
| 2 | Nhìn thanh địa chỉ sau khi trang trợ lý tải xong | URL đã sạch thành `/tro-ly` (do `replaceState` có sẵn) |
| 3 | Mở `/thu-tuc/DD-02` (tên có dấu phẩy) → bấm nút | Câu hỏi được encode đúng, không vỡ URL, trả lời khớp thủ tục cấp đổi sổ đỏ |

Nếu backend không với tới được thì ghi nhận là chưa kiểm được, không bỏ qua im lặng.

- [ ] **Step 4: Chạy lại toàn bộ test đơn vị**

Run: `cd frontend-next && npm test`
Expected: `# fail 0`

- [ ] **Step 5: Commit và push**

```bash
git add "frontend-next/src/app/thu-tuc/[code]/page.tsx"
git commit -m "feat(fe): nút hỏi trợ lý ở trang chi tiết mang câu hỏi theo

Trước đây link trống sang /tro-ly, người dân phải gõ lại từ đầu."
git push origin main
```

---

## Ngoài phạm vi plan này

- Mục "Quy trình các bước" ở trang chi tiết (chờ nguồn chính thức từ UBND xã)
- Tìm kiếm xuyên 225 bản ghi KB ở trang danh mục
- Lưu bộ lọc vào URL / chia sẻ link kết quả lọc
- Đồng bộ tính năng sang bản offline dự phòng
- Sửa phân loại XN-01 "Xác nhận tình trạng hôn nhân" đang nằm ở lĩnh vực "Cư trú" (dữ liệu seed, cần bạn quyết)
- Nới `FREE_GUEST_TURNS` cho buổi thi (việc vận hành trên Railway)
