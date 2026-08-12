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
  proc({
    code: "KS-01",
    name: "Đăng ký khai sinh",
    category: "Hộ tịch",
    keywords: ["khai sinh", "làm giấy cho con"],
  }),
  proc({
    code: "KT-01",
    name: "Đăng ký kết hôn",
    category: "Hộ tịch",
    keywords: ["kết hôn", "đăng ký kết hôn"],
  }),
  proc({
    code: "CU-02",
    name: "Đăng ký tạm trú",
    category: "Cư trú",
    keywords: ["tạm trú", "gia hạn tạm trú"],
  }),
  proc({
    code: "DD-02",
    name: "Cấp đổi, cấp lại Giấy chứng nhận quyền sử dụng đất",
    category: "Đất đai",
    keywords: ["cấp lại sổ đỏ", "sổ đỏ bị mất"],
  }),
];

const NO_FILTER = { query: "", category: null };

test("không lọc gì thì trả về toàn bộ danh sách", () => {
  assert.equal(filterProcedures(FIXTURE, NO_FILTER).length, 4);
});

test("khoảng trắng thuần không tính là truy vấn", () => {
  assert.equal(
    filterProcedures(FIXTURE, { query: "   ", category: null }).length,
    4,
  );
});

test("khớp theo tên, gõ không dấu", () => {
  const got = filterProcedures(FIXTURE, { query: "khai sinh", category: null });
  assert.deepEqual(
    got.map((p) => p.code),
    ["KS-01"],
  );
});

test("khớp theo keywords, gõ không dấu — 'so do' ra thủ tục đất đai", () => {
  const got = filterProcedures(FIXTURE, { query: "so do", category: null });
  assert.deepEqual(
    got.map((p) => p.code),
    ["DD-02"],
  );
});

test("khớp theo mã thủ tục", () => {
  const got = filterProcedures(FIXTURE, { query: "cu-02", category: null });
  assert.deepEqual(
    got.map((p) => p.code),
    ["CU-02"],
  );
});

test("khớp theo tên lĩnh vực", () => {
  const got = filterProcedures(FIXTURE, { query: "dat dai", category: null });
  assert.deepEqual(
    got.map((p) => p.code),
    ["DD-02"],
  );
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
  assert.deepEqual(
    got.map((p) => p.code),
    ["KS-01"],
  );
});

test("nhiều token là AND — phải khớp tất cả", () => {
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "gia han tam tru", category: null }).map(
      (p) => p.code,
    ),
    ["CU-02"],
  );
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "khai sinh ket hon", category: null }),
    [],
  );
});

test("chip lĩnh vực lọc độc lập", () => {
  const got = filterProcedures(FIXTURE, { query: "", category: "Hộ tịch" });
  assert.deepEqual(
    got.map((p) => p.code),
    ["KS-01", "KT-01"],
  );
});

test("chip và ô tìm kiếm cộng dồn", () => {
  assert.deepEqual(
    filterProcedures(FIXTURE, { query: "dang ky", category: "Cư trú" }).map(
      (p) => p.code,
    ),
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
    [
      ["Hộ tịch", 2],
      ["Cư trú", 1],
      ["Đất đai", 1],
    ],
  );
});

test("categoryFacets gắn emoji, lĩnh vực lạ rơi về 📋", () => {
  const facets = categoryFacets([
    ...FIXTURE,
    proc({ code: "ZZ-01", category: "Lĩnh vực mới" }),
  ]);
  const found = facets.find((f) => f.category === "Lĩnh vực mới");
  assert.equal(found?.icon, "📋");
  assert.equal(categoryIcon("Hộ tịch"), "👨‍👩‍👧");
});

test("danh sách rỗng không làm vỡ facets", () => {
  assert.deepEqual(categoryFacets([]), []);
});
