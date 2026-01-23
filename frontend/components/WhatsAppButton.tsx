import Link from "next/link";
import { MessageCircle } from "lucide-react";
import { Product } from "@/lib/types";
import { cn } from "@/lib/utils";

interface WhatsAppButtonProps {
    product?: Product;
    categoryName?: string;
    className?: string;
    label?: string;
    size?: "sm" | "md" | "lg";
}

export function WhatsAppButton({
    product,
    categoryName,
    className,
    label = "שלח בוואטסאפ להצעת מחיר",
    size = "md",
}: WhatsAppButtonProps) {
    // Environment variable for phone number
    const phoneNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "972500000000";

    let message = "";

    if (product) {
        const productUrl = typeof window !== "undefined" ? window.location.href : "";
        message = `היי, אשמח להצעת מחיר עבור:
מוצר: ${product.title}
מק"ט: ${product.sku}
ספק: ${product.supplier}
קישור: ${productUrl}`;
    } else if (categoryName) {
        const catUrl = typeof window !== "undefined" ? window.location.href : "";
        message = `היי, אשמח לפרטים על מוצרים בקטגוריה: ${categoryName}
קישור: ${catUrl}`;
    } else {
        message = "היי, אשמח לפרטים נוספים.";
    }

    const encodedMessage = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodedMessage}`;

    const sizeClasses = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-4 py-2",
        lg: "px-6 py-3 text-lg font-medium",
    };

    return (
        <Link
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md bg-green-500 text-white transition-colors hover:bg-green-600",
                sizeClasses[size],
                className
            )}
        >
            <MessageCircle className="h-5 w-5" />
            <span>{label}</span>
        </Link>
    );
}
