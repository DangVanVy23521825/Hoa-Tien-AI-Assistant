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
