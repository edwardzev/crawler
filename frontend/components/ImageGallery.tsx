"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface ImageGalleryProps {
    images: string[];
    title: string;
}

export function ImageGallery({ images, title }: ImageGalleryProps) {
    // Ensure we have at least one image/placeholder logic handled by parent or here?
    // If images empty, parent usually renders placeholder. But let's be safe.
    const validImages = images.length > 0 ? images : [];
    const [selectedIndex, setSelectedIndex] = useState(0);

    if (validImages.length === 0) {
        return (
            <div className="flex aspect-square w-full items-center justify-center bg-gray-100 text-gray-400">
                תמונה חסרה
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Main Image */}
            <div className="relative aspect-square w-full overflow-hidden rounded-lg border bg-white">
                <img
                    src={validImages[selectedIndex]}
                    alt={title}
                    className="h-full w-full object-contain p-4"
                />
            </div>

            {/* Thumbnails */}
            {validImages.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                    {validImages.map((img, idx) => (
                        <button
                            key={idx}
                            onClick={() => setSelectedIndex(idx)}
                            className={cn(
                                "relative h-20 w-20 shrink-0 overflow-hidden rounded-md border bg-white",
                                selectedIndex === idx ? "ring-2 ring-blue-500" : "hover:border-blue-300"
                            )}
                        >
                            <img
                                src={img}
                                alt={`${title} - תמונה ${idx + 1}`}
                                className="h-full w-full object-contain p-1"
                            />
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
