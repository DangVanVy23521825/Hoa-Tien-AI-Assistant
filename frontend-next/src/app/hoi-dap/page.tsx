"use client";

import { useState, useEffect } from "react";
import { api, Faq } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function HoiDapPage() {
  const [faqs, setFaqs] = useState<Faq[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getFaq()
      .then(setFaqs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-4xl mx-auto px-6 py-14">
      <div className="mb-8">
        <Badge
          variant="secondary"
          className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
          Hỏi đáp
        </Badge>
        <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
          Câu hỏi thường gặp
        </h2>
        <p className="mt-2 text-ink-soft max-w-xl">
          Những thắc mắc phổ biến của người dân về giờ làm việc, nộp hồ sơ trực
          tuyến và thông tin xã.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-ink-soft">Đang tải...</div>
      ) : (
        <Accordion className="space-y-3">
          {faqs.map((faq) => (
            <AccordionItem
              key={faq.id}
              value={faq.id}
              className="bg-white border border-line rounded-xl px-5 data-open:shadow-sm"
            >
              <AccordionTrigger className="text-left font-semibold text-[15px] hover:text-paddy-deep hover:no-underline py-4">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-ink-soft text-sm pb-4">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </section>
  );
}
