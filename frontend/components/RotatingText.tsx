"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const PHRASES = [
    "כל הספקים",
    "כל המחירים",
    "כל המלאים"
];

export function RotatingText() {
    const [index, setIndex] = useState(0);
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const intervalId = setInterval(() => {
            // Fade out
            setIsVisible(false);

            // Wait for transition, then swap text and fade in
            setTimeout(() => {
                setIndex((prev) => (prev + 1) % PHRASES.length);
                setIsVisible(true);
            }, 700); // Wait 700ms for fade out

        }, 2500); // Change every 2.5 seconds

        return () => clearInterval(intervalId);
    }, []);

    return (
        <span className="block h-[1.2em] overflow-hidden text-blue-600">
            <span
                className={cn(
                    "block transition-all duration-700 ease-in-out transform",
                    isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                )}
            >
                {PHRASES[index]}
            </span>
        </span>
    );
}
