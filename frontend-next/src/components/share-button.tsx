"use client";

import { useState } from "react";
import { qr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Share2, Check } from "lucide-react";

/** Mobile: sheet chia sẻ hệ thống (có sẵn Zalo/Messenger).
    Desktop: hiện QR + nút sao chép link. */
export default function ShareButton() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [url, setUrl] = useState("");

  const handleShare = async () => {
    const current = window.location.href.split("#")[0];
    setUrl(current);

    if (navigator.share) {
      try {
        await navigator.share({
          title: "Hòa Tiến AI · Trợ lý hành chính số",
          url: current,
        });
      } catch {}
      return;
    }
    setOpen((v) => !v);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="lg"
        onClick={handleShare}
        className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
      >
        <Share2 className="w-4 h-4" />
        Chia sẻ
      </Button>

      {open && (
        <div className="absolute z-40 mt-2 bg-white border border-line rounded-xl p-4 shadow-lg text-center w-48">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={qr(url, 110)}
            alt="QR chia sẻ trang"
            className="w-[110px] h-[110px] mx-auto rounded"
          />
          <small className="block mt-2 text-xs text-ink-soft">
            Quét để mở trên điện thoại
          </small>
          <button
            onClick={handleCopy}
            className="mt-2 w-full text-xs font-semibold text-paddy-deep hover:underline inline-flex items-center justify-center gap-1"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5" />
                Đã sao chép
              </>
            ) : (
              "Sao chép liên kết"
            )}
          </button>
        </div>
      )}
    </div>
  );
}
